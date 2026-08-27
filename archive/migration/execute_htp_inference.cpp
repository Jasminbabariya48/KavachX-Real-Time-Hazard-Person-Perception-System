#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <chrono>
#include <cmath>
#include <algorithm>
#include <dlfcn.h>

#include "QnnInterface.h"
#include "QnnBackend.h"
#include "QnnDevice.h"
#include "QnnContext.h"
#include "QnnGraph.h"
#include "QnnTensor.h"
#include "System/QnnSystemInterface.h"
#include "System/QnnSystemContext.h"

struct Detection {
    float x1, y1, x2, y2;
    float score;
    int classId;
};

// Compute IoU
static float computeIoU(const Detection& a, const Detection& b) {
    float x1 = std::max(a.x1, b.x1);
    float y1 = std::max(a.y1, b.y1);
    float x2 = std::min(a.x2, b.x2);
    float y2 = std::min(a.y2, b.y2);
    float w = std::max(0.0f, x2 - x1);
    float h = std::max(0.0f, y2 - y1);
    float inter = w * h;
    float areaA = (a.x2 - a.x1) * (a.y2 - a.y1);
    float areaB = (b.x2 - b.x1) * (b.y2 - b.y1);
    float unionArea = areaA + areaB - inter;
    return unionArea > 0.0f ? (inter / unionArea) : 0.0f;
}

// NMS
static std::vector<Detection> runNMS(std::vector<Detection>& dets, float iouThreshold) {
    std::sort(dets.begin(), dets.end(), [](const Detection& a, const Detection& b) {
        return a.score > b.score;
    });
    std::vector<Detection> result;
    std::vector<bool> suppressed(dets.size(), false);
    for (size_t i = 0; i < dets.size(); ++i) {
        if (suppressed[i]) continue;
        result.push_back(dets[i]);
        for (size_t j = i + 1; j < dets.size(); ++j) {
            if (!suppressed[j] && dets[i].classId == dets[j].classId) {
                if (computeIoU(dets[i], dets[j]) >= iouThreshold) {
                    suppressed[j] = true;
                }
            }
        }
    }
    return result;
}

// Vectorized CPU DFL decoding for YOLOv8
static std::vector<Detection> decodeYOLOv8DFL(
    const float* bboxDist,  // [1, 64, 8400]
    const float* clsScores, // [1, 3, 8400]
    float confThreshold = 0.25f,
    float iouThreshold = 0.45f)
{
    // Generate anchor points and stride factors for strides 8, 16, 32
    // 640x640 input -> 80x80 (6400), 40x40 (1600), 20x20 (400) = 8400 anchors
    std::vector<float> anchorX(8400);
    std::vector<float> anchorY(8400);
    std::vector<float> stride(8400);

    size_t idx = 0;
    int strides[3] = {8, 16, 32};
    int gridSizes[3] = {80, 40, 20};

    for (int s = 0; s < 3; ++s) {
        int g = gridSizes[s];
        int str = strides[s];
        for (int y = 0; y < g; ++y) {
            for (int x = 0; x < g; ++x) {
                anchorX[idx] = (float)x + 0.5f;
                anchorY[idx] = (float)y + 0.5f;
                stride[idx]  = (float)str;
                idx++;
            }
        }
    }

    std::vector<Detection> candidates;

    for (int a = 0; a < 8400; ++a) {
        // Find best class
        float maxScore = -1.0f;
        int bestCls = -1;
        for (int c = 0; c < 3; ++c) {
            float s = clsScores[c * 8400 + a];
            if (s > maxScore) {
                maxScore = s;
                bestCls = c;
            }
        }

        if (maxScore < confThreshold) continue;

        // DFL decode 4 coordinates (left, top, right, bottom) from 16 bins each
        float dist[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        for (int coord = 0; coord < 4; ++coord) {
            float expSum = 0.0f;
            float expVals[16];
            float maxBin = -1e9f;
            for (int bin = 0; bin < 16; ++bin) {
                float val = bboxDist[(coord * 16 + bin) * 8400 + a];
                if (val > maxBin) maxBin = val;
            }
            for (int bin = 0; bin < 16; ++bin) {
                float val = bboxDist[(coord * 16 + bin) * 8400 + a];
                expVals[bin] = std::exp(val - maxBin);
                expSum += expVals[bin];
            }
            float weightedSum = 0.0f;
            for (int bin = 0; bin < 16; ++bin) {
                float prob = expVals[bin] / expSum;
                weightedSum += prob * (float)bin;
            }
            dist[coord] = weightedSum;
        }

        // Project distances to input image coordinates
        float ax = anchorX[a];
        float ay = anchorY[a];
        float str = stride[a];

        float x1 = (ax - dist[0]) * str;
        float y1 = (ay - dist[1]) * str;
        float x2 = (ax + dist[2]) * str;
        float y2 = (ay + dist[3]) * str;

        x1 = std::max(0.0f, std::min(640.0f, x1));
        y1 = std::max(0.0f, std::min(640.0f, y1));
        x2 = std::max(0.0f, std::min(640.0f, x2));
        y2 = std::max(0.0f, std::min(640.0f, y2));

        if (x2 > x1 && y2 > y1) {
            candidates.push_back({x1, y1, x2, y2, maxScore, bestCls});
        }
    }

    return runNMS(candidates, iouThreshold);
}

int main(int argc, char** argv) {
    if (argc < 6) {
        printf("Usage: %s <backend.so> <system.so> <model.bin> <input_uint8.raw> <output_prefix>\n", argv[0]);
        return 1;
    }
    const char* backendPath = argv[1];
    const char* systemPath  = argv[2];
    const char* modelPath   = argv[3];
    const char* inputRaw    = argv[4];
    const char* outPrefix   = argv[5];

    printf("====================================================\n");
    printf("  KavachX Step 7 — Real Qualcomm Hexagon HTP Inference\n");
    printf("====================================================\n");
    printf("Backend: %s\n", backendPath);
    printf("System:  %s\n", systemPath);
    printf("Model:   %s\n", modelPath);
    printf("Input:   %s\n", inputRaw);
    printf("----------------------------------------------------\n");

    // 1. Load Libraries
    void* backendLib = dlopen(backendPath, RTLD_NOW | RTLD_LOCAL);
    void* systemLib  = dlopen(systemPath, RTLD_NOW | RTLD_LOCAL);
    if (!backendLib || !systemLib) {
        fprintf(stderr, "dlopen failed: %s\n", dlerror());
        return 1;
    }

    typedef Qnn_ErrorHandle_t (*GetProvidersFn)(const QnnInterface_t***, uint32_t*);
    auto getProviders = (GetProvidersFn)dlsym(backendLib, "QnnInterface_getProviders");
    const QnnInterface_t** providers = nullptr;
    uint32_t numProviders = 0;
    getProviders(&providers, &numProviders);
    QnnInterface_t qnnIf = *providers[0];

    typedef Qnn_ErrorHandle_t (*GetSysProvidersFn)(const QnnSystemInterface_t***, uint32_t*);
    auto getSysProviders = (GetSysProvidersFn)dlsym(systemLib, "QnnSystemInterface_getProviders");
    const QnnSystemInterface_t** sysProviders = nullptr;
    uint32_t numSysProviders = 0;
    getSysProviders(&sysProviders, &numSysProviders);
    QnnSystemInterface_t sysIf = *sysProviders[0];

    // 2. Create Backend & HTP Device
    Qnn_BackendHandle_t backend = nullptr;
    qnnIf.QNN_INTERFACE_VER_NAME.backendCreate(nullptr, nullptr, &backend);

    Qnn_DeviceHandle_t device = nullptr;
    const QnnDevice_Config_t* devCfg[] = {nullptr};
    qnnIf.QNN_INTERFACE_VER_NAME.deviceCreate(nullptr, devCfg, &device);

    // 3. Load Context from Binary
    FILE* f = fopen(modelPath, "rb");
    fseek(f, 0, SEEK_END);
    size_t binSize = ftell(f);
    fseek(f, 0, SEEK_SET);
    void* binBuffer = malloc(binSize);
    size_t r = fread(binBuffer, 1, binSize, f);
    (void)r;
    fclose(f);

    QnnSystemContext_Handle_t sysCtx = nullptr;
    sysIf.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextCreate(&sysCtx);
    const QnnSystemContext_BinaryInfo_t* binInfo = nullptr;
    Qnn_ContextBinarySize_t binInfoSize = 0;
    sysIf.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextGetBinaryInfo(
        sysCtx, binBuffer, (Qnn_ContextBinarySize_t)binSize, &binInfo, &binInfoSize);

    const QnnSystemContext_GraphInfo_t* graphs = binInfo->contextBinaryInfoV3.graphs;
    const char* graphName = graphs[0].graphInfoV3.graphName;
    uint32_t numInputs  = graphs[0].graphInfoV3.numGraphInputs;
    uint32_t numOutputs = graphs[0].graphInfoV3.numGraphOutputs;
    Qnn_Tensor_t* inTemplates  = graphs[0].graphInfoV3.graphInputs;
    Qnn_Tensor_t* outTemplates = graphs[0].graphInfoV3.graphOutputs;

    printf("Graph Name: '%s', Inputs: %u, Outputs: %u\n", graphName, numInputs, numOutputs);

    Qnn_ContextHandle_t context = nullptr;
    const QnnContext_Config_t* ctxCfg[] = {nullptr};
    qnnIf.QNN_INTERFACE_VER_NAME.contextCreateFromBinary(
        backend, device, ctxCfg, binBuffer, (Qnn_ContextBinarySize_t)binSize, &context, nullptr);

    Qnn_GraphHandle_t graph = nullptr;
    qnnIf.QNN_INTERFACE_VER_NAME.graphRetrieve(context, graphName, &graph);

    // 4. Setup Input/Output Tensors
    std::vector<Qnn_Tensor_t> inputTensors(numInputs);
    for (uint32_t i = 0; i < numInputs; ++i) {
        inputTensors[i] = inTemplates[i];
        size_t tensorBytes = 1 * 3 * 640 * 640; // uint8
        void* buf = malloc(tensorBytes);
        inputTensors[i].v1.memType = QNN_TENSORMEMTYPE_RAW;
        inputTensors[i].v1.clientBuf.data = buf;
        inputTensors[i].v1.clientBuf.dataSize = (uint32_t)tensorBytes;
    }

    std::vector<Qnn_Tensor_t> outputTensors(numOutputs);
    std::vector<std::vector<uint8_t>> rawOutputBuffers(numOutputs);
    std::vector<float> scales(numOutputs);
    std::vector<int32_t> offsets(numOutputs);

    for (uint32_t i = 0; i < numOutputs; ++i) {
        outputTensors[i] = outTemplates[i];
        size_t count = 1;
        for (uint32_t d = 0; d < outTemplates[i].v1.rank; ++d) {
            count *= outTemplates[i].v1.dimensions[d];
        }
        rawOutputBuffers[i].resize(count);
        outputTensors[i].v1.memType = QNN_TENSORMEMTYPE_RAW;
        outputTensors[i].v1.clientBuf.data = rawOutputBuffers[i].data();
        outputTensors[i].v1.clientBuf.dataSize = (uint32_t)count;

        scales[i]  = outTemplates[i].v1.quantizeParams.scaleOffsetEncoding.scale;
        offsets[i] = outTemplates[i].v1.quantizeParams.scaleOffsetEncoding.offset;
        printf("Output[%u] '%s': count=%zu bytes, scale=%e, offset=%d\n",
               i, outTemplates[i].v1.name, count, scales[i], offsets[i]);
    }

    // 5. Load Input Data
    FILE* fin = fopen(inputRaw, "rb");
    if (!fin) {
        fprintf(stderr, "Cannot open input raw file: %s\n", inputRaw);
        return 1;
    }
    size_t inRead = fread(inputTensors[0].v1.clientBuf.data, 1, inputTensors[0].v1.clientBuf.dataSize, fin);
    (void)inRead;
    fclose(fin);
    printf("Loaded input raw data (%u bytes)\n", inputTensors[0].v1.clientBuf.dataSize);

    // 6. Warm-up
    printf("[Warm-up] Executing 5 warm-up iterations on Hexagon HTP...\n");
    for (int w = 0; w < 5; ++w) {
        qnnIf.QNN_INTERFACE_VER_NAME.graphExecute(
            graph, inputTensors.data(), numInputs, outputTensors.data(), numOutputs, nullptr, nullptr);
    }

    // 7. Benchmark Real HTP Execution (100 runs)
    printf("[Benchmark] Executing 100 benchmark iterations on Hexagon HTP...\n");
    std::vector<double> latencies;
    latencies.reserve(100);

    for (int r = 0; r < 100; ++r) {
        auto t0 = std::chrono::high_resolution_clock::now();
        Qnn_ErrorHandle_t execErr = qnnIf.QNN_INTERFACE_VER_NAME.graphExecute(
            graph, inputTensors.data(), numInputs, outputTensors.data(), numOutputs, nullptr, nullptr);
        auto t1 = std::chrono::high_resolution_clock::now();
        if (execErr != QNN_SUCCESS) {
            fprintf(stderr, "graphExecute failed at iter %d: %llu\n", r, (unsigned long long)execErr);
            return 1;
        }
        double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        latencies.push_back(ms);
    }

    std::sort(latencies.begin(), latencies.end());
    double sum = 0.0;
    for (double l : latencies) sum += l;
    double meanMs = sum / latencies.size();
    double minMs  = latencies.front();
    double maxMs  = latencies.back();
    double p50Ms  = latencies[latencies.size() * 50 / 100];
    double p95Ms  = latencies[latencies.size() * 95 / 100];
    double p99Ms  = latencies[latencies.size() * 99 / 100];
    double fps    = 1000.0 / meanMs;

    printf("\n=== HEXAGON v68 HTP EXECUTION LATENCY (100 runs) ===\n");
    printf("  Mean:   %.2f ms (%.1f FPS)\n", meanMs, fps);
    printf("  Median: %.2f ms\n", p50Ms);
    printf("  Min:    %.2f ms\n", minMs);
    printf("  Max:    %.2f ms\n", maxMs);
    printf("  P95:    %.2f ms\n", p95Ms);
    printf("  P99:    %.2f ms\n", p99Ms);

    // 8. Dequantize Outputs: float = (uint8 + offset) * scale
    std::vector<float> dequantBbox(rawOutputBuffers[0].size());
    for (size_t k = 0; k < rawOutputBuffers[0].size(); ++k) {
        dequantBbox[k] = ((float)((int32_t)rawOutputBuffers[0][k] + offsets[0])) * scales[0];
    }

    std::vector<float> dequantCls(rawOutputBuffers[1].size());
    for (size_t k = 0; k < rawOutputBuffers[1].size(); ++k) {
        dequantCls[k] = ((float)((int32_t)rawOutputBuffers[1][k] + offsets[1])) * scales[1];
    }

    // Save Raw Outputs & Dequantized Floats
    std::string bboxUint8File = std::string(outPrefix) + "_bbox_htp_uint8.raw";
    std::string clsUint8File  = std::string(outPrefix) + "_class_htp_uint8.raw";
    std::string bboxFp32File  = std::string(outPrefix) + "_bbox_htp_dequant.raw";
    std::string clsFp32File   = std::string(outPrefix) + "_class_htp_dequant.raw";

    FILE* fbu = fopen(bboxUint8File.c_str(), "wb");
    fwrite(rawOutputBuffers[0].data(), 1, rawOutputBuffers[0].size(), fbu);
    fclose(fbu);

    FILE* fcu = fopen(clsUint8File.c_str(), "wb");
    fwrite(rawOutputBuffers[1].data(), 1, rawOutputBuffers[1].size(), fcu);
    fclose(fcu);

    FILE* fbf = fopen(bboxFp32File.c_str(), "wb");
    fwrite(dequantBbox.data(), sizeof(float), dequantBbox.size(), fbf);
    fclose(fbf);

    FILE* fcf = fopen(clsFp32File.c_str(), "wb");
    fwrite(dequantCls.data(), sizeof(float), dequantCls.size(), fcf);
    fclose(fcf);

    printf("\nSaved raw HTP and dequantized outputs:\n  %s\n  %s\n  %s\n  %s\n",
           bboxUint8File.c_str(), clsUint8File.c_str(), bboxFp32File.c_str(), clsFp32File.c_str());

    // 9. CPU DFL Decoding & NMS
    auto dflStart = std::chrono::high_resolution_clock::now();
    std::vector<Detection> detections = decodeYOLOv8DFL(dequantBbox.data(), dequantCls.data(), 0.25f, 0.45f);
    auto dflEnd = std::chrono::high_resolution_clock::now();
    double dflMs = std::chrono::duration<double, std::milli>(dflEnd - dflStart).count();

    const char* classNames[3] = {"fire", "smoke", "person"};
    printf("\n=== DETECTIONS (%zu found, CPU DFL/NMS: %.2f ms) ===\n", detections.size(), dflMs);
    for (size_t d = 0; d < detections.size(); ++d) {
        const auto& det = detections[d];
        const char* cname = (det.classId >= 0 && det.classId < 3) ? classNames[det.classId] : "unknown";
        printf("  [%zu] Class: %s (id=%d), Conf: %.3f, Box: [%.1f, %.1f, %.1f, %.1f]\n",
               d, cname, det.classId, det.score, det.x1, det.y1, det.x2, det.y2);
    }

    // 10. Write JSON Summary
    std::string jsonFile = std::string(outPrefix) + "_summary.json";
    FILE* fj = fopen(jsonFile.c_str(), "w");
    fprintf(fj, "{\n");
    fprintf(fj, "  \"image\": \"%s\",\n", inputRaw);
    fprintf(fj, "  \"model\": \"%s\",\n", modelPath);
    fprintf(fj, "  \"htp_execution_status\": \"PASS\",\n");
    fprintf(fj, "  \"benchmark_100_runs\": {\n");
    fprintf(fj, "    \"mean_ms\": %.2f,\n", meanMs);
    fprintf(fj, "    \"median_ms\": %.2f,\n", p50Ms);
    fprintf(fj, "    \"min_ms\": %.2f,\n", minMs);
    fprintf(fj, "    \"max_ms\": %.2f,\n", maxMs);
    fprintf(fj, "    \"p95_ms\": %.2f,\n", p95Ms);
    fprintf(fj, "    \"p99_ms\": %.2f,\n", p99Ms);
    fprintf(fj, "    \"fps\": %.1f\n", fps);
    fprintf(fj, "  },\n");
    fprintf(fj, "  \"cpu_dfl_nms_ms\": %.2f,\n", dflMs);
    fprintf(fj, "  \"total_end_to_end_ms\": %.2f,\n", meanMs + dflMs);
    fprintf(fj, "  \"detections_count\": %zu,\n", detections.size());
    fprintf(fj, "  \"detections\": [\n");
    for (size_t d = 0; d < detections.size(); ++d) {
        const auto& det = detections[d];
        const char* cname = (det.classId >= 0 && det.classId < 3) ? classNames[det.classId] : "unknown";
        fprintf(fj, "    {\"class_id\": %d, \"class_name\": \"%s\", \"score\": %.4f, \"bbox\": [%.1f, %.1f, %.1f, %.1f]}%s\n",
                det.classId, cname, det.score, det.x1, det.y1, det.x2, det.y2, (d + 1 < detections.size() ? "," : ""));
    }
    fprintf(fj, "  ]\n");
    fprintf(fj, "}\n");
    fclose(fj);
    printf("Summary written to %s\n", jsonFile.c_str());

    // Clean up
    sysIf.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextFree(sysCtx);
    qnnIf.QNN_INTERFACE_VER_NAME.contextFree(context, nullptr);
    qnnIf.QNN_INTERFACE_VER_NAME.deviceFree(device);
    qnnIf.QNN_INTERFACE_VER_NAME.backendFree(backend);
    free(binBuffer);
    for (auto& t : inputTensors) free(t.v1.clientBuf.data);
    dlclose(backendLib);
    dlclose(systemLib);

    return 0;
}
