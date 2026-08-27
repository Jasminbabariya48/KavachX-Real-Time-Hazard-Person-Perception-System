"""
live_monitoring_server.py
-------------------------
Lightweight HTTP Server providing live MJPEG stream and telemetry dashboard for KavachX.
"""

import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>KavachX NPU — Live Stream Monitoring</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 15px; margin-bottom: 20px; }
        .badge { background: #0284c7; color: white; padding: 4px 12px; border-radius: 9999px; font-weight: bold; font-size: 0.85rem; }
        .badge-success { background: #16a34a; }
        .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        .card { background: #1e293b; border-radius: 12px; padding: 16px; border: 1px solid #334155; }
        .video-container { width: 100%; border-radius: 8px; overflow: hidden; background: #000; display: flex; justify-content: center; align-items: center; min-height: 480px; }
        .video-container img { width: 100%; height: auto; display: block; }
        .metric-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; }
        .metric-box { background: #0f172a; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #1e293b; }
        .metric-val { font-size: 1.5rem; font-weight: bold; color: #38bdf8; }
        .metric-lbl { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; margin-top: 4px; }
        .alert-item { background: #0f172a; padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 4px solid #f59e0b; font-size: 0.85rem; }
        .alert-critical { border-left-color: #ef4444; }
        .alert-title { font-weight: bold; display: flex; justify-content: space-between; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🛡️ KavachX Qualcomm Hexagon v68 HTP — Live Stream Monitor</h2>
        <div>
            <span class="badge badge-success" id="state-badge">HTP ACTIVE</span>
            <span class="badge" id="fps-badge">0.0 FPS</span>
        </div>
    </div>
    <div class="grid">
        <div class="card">
            <div class="video-container">
                <img src="/video_feed" alt="Live Camera / Stream Stream" />
            </div>
        </div>
        <div>
            <div class="card" style="margin-bottom: 20px;">
                <h3 style="margin-top:0;">⚡ Live Performance</h3>
                <div class="metric-row">
                    <div class="metric-box">
                        <div class="metric-val" id="metric-fps">0.0</div>
                        <div class="metric-lbl">Inference FPS</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-val" id="metric-htp">0.0 ms</div>
                        <div class="metric-lbl">HTP Latency</div>
                    </div>
                </div>
                <div class="metric-row">
                    <div class="metric-box">
                        <div class="metric-val" id="metric-e2e">0.0 ms</div>
                        <div class="metric-lbl">End-to-End Latency</div>
                    </div>
                    <div class="metric-box">
                        <div class="metric-val" id="metric-frames">0</div>
                        <div class="metric-lbl">Frames Processed</div>
                    </div>
                </div>
            </div>
            <div class="card">
                <h3 style="margin-top:0;">🚨 Downstream Alerts</h3>
                <div id="alerts-container" style="max-height: 260px; overflow-y: auto;">
                    <div style="color: #64748b; text-align: center; padding: 20px;">No hazard events detected</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        setInterval(() => {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('metric-fps').innerText = data.inference_fps.toFixed(1);
                    document.getElementById('fps-badge').innerText = data.inference_fps.toFixed(1) + ' FPS';
                    document.getElementById('metric-htp').innerText = data.mean_htp_latency_ms.toFixed(1) + ' ms';
                    document.getElementById('metric-e2e').innerText = data.mean_e2e_latency_ms.toFixed(1) + ' ms';
                    document.getElementById('metric-frames').innerText = data.processed_frames;
                    
                    const container = document.getElementById('alerts-container');
                    if (data.recent_alerts && data.recent_alerts.length > 0) {
                        container.innerHTML = data.recent_alerts.slice(-6).reverse().map(a => `
                            <div class="alert-item ${a.severity === 'CRITICAL' ? 'alert-critical' : ''}">
                                <div class="alert-title">
                                    <span>${a.event_type} (${a.class_name.toUpperCase()})</span>
                                    <span>${a.confidence.toFixed(2)}</span>
                                </div>
                                <div style="color: #94a3b8; font-size: 0.75rem; margin-top: 4px;">
                                    ${a.timestamp} | Frame #${a.frame_id}
                                </div>
                            </div>
                        `).join('');
                    }
                })
                .catch(e => console.error(e));
        }, 1000);
    </script>
</body>
</html>
"""

class MonitoringHandler(BaseHTTPRequestHandler):
    pipeline = None

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode('utf-8'))
        elif self.path == '/api/stats':
            stats = self.pipeline.stats
            lats = stats.get("recent_latencies_ms", [])
            e2e = stats.get("recent_e2e_latencies_ms", [])
            import numpy as np
            resp = {
                "captured_frames": stats.get("captured_frames", 0),
                "processed_frames": stats.get("processed_frames", 0),
                "dropped_frames": stats.get("dropped_frames", 0),
                "inference_fps": stats.get("inference_fps", 0.0),
                "mean_htp_latency_ms": float(np.mean(lats)) if lats else 0.0,
                "mean_e2e_latency_ms": float(np.mean(e2e)) if e2e else 0.0,
                "recent_alerts": self.pipeline.recent_alerts[-10:],
                "cpu_fallback_count": 0
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode('utf-8'))
        elif self.path == '/video_feed':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            while self.pipeline.is_running:
                jpeg_bytes = self.pipeline.get_latest_frame_jpeg()
                self.wfile.write(b'--frame\r\n')
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(len(jpeg_bytes)))
                self.end_headers()
                self.wfile.write(jpeg_bytes)
                self.wfile.write(b'\r\n')
                time.sleep(0.033)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass # Suppress logging each frame HTTP request

def start_monitoring_server(pipeline, port=8080):
    MonitoringHandler.pipeline = pipeline
    server = HTTPServer(('0.0.0.0', port), MonitoringHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"[MonitoringUI] Live Web UI server running on http://0.0.0.0:{port}")
    return server
