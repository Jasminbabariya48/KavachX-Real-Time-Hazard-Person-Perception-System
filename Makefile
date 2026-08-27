.PHONY: all build test clean health demo

all: build

build:
	@echo "Building native NPU worker..."
	@cd native/worker && make clean && make -j$$(nproc)

test:
	@echo "Running test suite..."
	@PYTHONPATH=src python3 tests/hardware/test_htp_inference.py
	@PYTHONPATH=src python3 tests/integration/test_pipeline_integration.py
	@PYTHONPATH=src python3 tests/streaming/test_live_stream.py

demo:
	@bash deployment/run_demo.sh

health:
	@cat /tmp/kawach_health.json 2>/dev/null || echo "Worker is stopped"
