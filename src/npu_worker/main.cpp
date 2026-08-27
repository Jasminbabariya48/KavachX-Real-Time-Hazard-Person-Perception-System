/*
 * main.cpp
 * --------
 * Kawach NPU Production Worker — persistent high-performance daemon
 * serving inference requests over Unix domain socket with QNN HTP v68 acceleration.
 */

#include "qnn_inference.hpp"
#include "ipc_handler.hpp"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <csignal>
#include <chrono>
#include <string>
#include <vector>
#include <unistd.h>

static volatile bool g_running = true;

static void signalHandler(int sig) {
    fprintf(stdout, "\n[kawach_worker] Received signal %d, shutting down cleanly...\n", sig);
    g_running = false;
}

static void printUsage(const char* progName) {
    fprintf(stderr,
        "Usage: %s --backend <libQnnHtp.so> --system <libQnnSystem.so> "
        "--model <model.bin> [--socket <path>]\n\n"
        "Options:\n"
        "  --backend  Path to QNN HTP backend library\n"
        "  --system   Path to QNN System library\n"
        "  --model    Path to compiled model context binary\n"
        "  --socket   Unix socket path (default: /tmp/kawach_worker.sock)\n",
        progName);
}

struct Args {
    std::string backendPath;
    std::string systemPath;
    std::string modelPath;
    std::string socketPath = "/tmp/kawach_worker.sock";
};

static bool parseArgs(int argc, char* argv[], Args& args) {
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--backend") == 0 && i + 1 < argc) {
            args.backendPath = argv[++i];
        } else if (strcmp(argv[i], "--system") == 0 && i + 1 < argc) {
            args.systemPath = argv[++i];
        } else if (strcmp(argv[i], "--model") == 0 && i + 1 < argc) {
            args.modelPath = argv[++i];
        } else if (strcmp(argv[i], "--socket") == 0 && i + 1 < argc) {
            args.socketPath = argv[++i];
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            printUsage(argv[0]);
            exit(0);
        } else {
            fprintf(stderr, "Unknown argument: %s\n", argv[i]);
            printUsage(argv[0]);
            return false;
        }
    }

    if (args.backendPath.empty() || args.systemPath.empty() || args.modelPath.empty()) {
        fprintf(stderr, "Error: --backend, --system, and --model are required\n");
        printUsage(argv[0]);
        return false;
    }
    return true;
}

int main(int argc, char* argv[]) {
    Args args;
    if (!parseArgs(argc, argv, args)) return 1;

    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);
    signal(SIGPIPE, SIG_IGN); // Prevent termination on broken socket pipe

    fprintf(stdout, "====================================================\n");
    fprintf(stdout, "  KawachX NPU Production Worker v1.0\n");
    fprintf(stdout, "====================================================\n");
    fprintf(stdout, "Backend: %s\n", args.backendPath.c_str());
    fprintf(stdout, "System:  %s\n", args.systemPath.c_str());
    fprintf(stdout, "Model:   %s\n", args.modelPath.c_str());
    fprintf(stdout, "Socket:  %s\n", args.socketPath.c_str());
    fprintf(stdout, "====================================================\n\n");

    // 1. Initialize QNN HTP (ONCE at daemon startup)
    kawach::QnnInference engine;
    auto initStart = std::chrono::steady_clock::now();

    kawach::Status initStatus = engine.initialize(
        args.backendPath, args.systemPath, args.modelPath);

    auto initEnd = std::chrono::steady_clock::now();
    double initMs = std::chrono::duration<double, std::milli>(initEnd - initStart).count();

    if (initStatus != kawach::Status::SUCCESS) {
        fprintf(stderr, "[kawach_worker] FATAL: QNN HTP init failed: %s\n",
                kawach::statusString(initStatus));
        return 2;
    }
    fprintf(stdout, "[kawach_worker] QNN HTP initialized successfully in %.1f ms\n\n", initMs);

    // 2. Open IPC socket
    kawach::IpcHandler ipc;
    if (!ipc.listen(args.socketPath)) {
        fprintf(stderr, "[kawach_worker] FATAL: Failed to create IPC socket\n");
        return 3;
    }

    // 3. Pre-allocated working buffers
    std::vector<uint8_t> inputBuffer(kawach::INPUT_SIZE);
    std::vector<float> outputBuffer(kawach::OUTPUT_SIZE);

    uint64_t totalRequests = 0;
    uint64_t successRequests = 0;
    uint64_t failedRequests = 0;
    double totalInferMs = 0.0;

    while (g_running) {
        if (!ipc.acceptClient(500)) {
            continue; // Poll timeout, loop check g_running
        }

        fprintf(stdout, "[kawach_worker] Client connected\n");

        while (g_running && ipc.hasClient()) {
            // Peek or read initial 4 bytes to check for framed header vs legacy raw stream
            uint32_t firstWord = 0;
            ssize_t n = ipc.readExact(&firstWord, sizeof(firstWord), 5000);
            if (n == 0) {
                // Client closed cleanly
                fprintf(stdout, "[kawach_worker] Client disconnected\n");
                ipc.closeClient();
                break;
            }
            if (n < 0) {
                fprintf(stderr, "[kawach_worker] Socket read error, closing client\n");
                ipc.closeClient();
                break;
            }

            uint32_t reqId = 0;
            size_t payloadNeeded = 0;

            if (firstWord == kawach::IPC_MAGIC_REQUEST) {
                // Framed protocol: read remainder of header
                kawach::IpcRequestHeader reqHdr;
                reqHdr.magic = firstWord;
                ssize_t hdrRem = ipc.readExact(((uint8_t*)&reqHdr) + sizeof(firstWord),
                                               sizeof(reqHdr) - sizeof(firstWord), 2000);
                if (hdrRem < 0) {
                    fprintf(stderr, "[kawach_worker] Truncated header received\n");
                    ipc.closeClient();
                    break;
                }
                reqId = reqHdr.requestId;
                payloadNeeded = reqHdr.payloadSize;
            } else {
                // Legacy unadorned raw stream: first 4 bytes were start of image
                reqId = (uint32_t)totalRequests + 1;
                std::memcpy(inputBuffer.data(), &firstWord, sizeof(firstWord));
                payloadNeeded = kawach::INPUT_SIZE - sizeof(firstWord);
            }

            totalRequests++;

            if (payloadNeeded > kawach::INPUT_SIZE) {
                fprintf(stderr, "[kawach_worker] Error: Oversized payload requested (%zu bytes)\n", payloadNeeded);
                failedRequests++;
                uint32_t errStatus = 1; // BAD_PAYLOAD
                ipc.writeExact(&errStatus, sizeof(errStatus));
                continue;
            }

            // Read payload
            uint8_t* destPtr = (firstWord == kawach::IPC_MAGIC_REQUEST) ? inputBuffer.data() : (inputBuffer.data() + sizeof(firstWord));
            ssize_t payloadRead = ipc.readExact(destPtr, payloadNeeded, 5000);
            if (payloadRead < 0) {
                fprintf(stderr, "[kawach_worker] Truncated payload for req #%u\n", reqId);
                failedRequests++;
                ipc.closeClient();
                break;
            }

            // Execute HTP Inference & CPU DFL Post-Processing
            auto t0 = std::chrono::high_resolution_clock::now();
            kawach::Status execStatus = engine.infer(inputBuffer.data(), outputBuffer.data());
            auto t1 = std::chrono::high_resolution_clock::now();
            double inferMs = std::chrono::duration<double, std::milli>(t1 - t0).count();

            if (execStatus != kawach::Status::SUCCESS) {
                fprintf(stderr, "[kawach_worker] HTP infer error for req #%u: %s\n",
                        reqId, kawach::statusString(execStatus));
                failedRequests++;
                uint32_t errStatus = 2; // INFER_ERROR
                ipc.writeExact(&errStatus, sizeof(errStatus));
                continue;
            }

            successRequests++;
            totalInferMs += inferMs;

            // Send Response
            if (firstWord == kawach::IPC_MAGIC_REQUEST) {
                kawach::IpcResponseHeader respHdr;
                respHdr.magic         = kawach::IPC_MAGIC_RESPONSE;
                respHdr.requestId     = reqId;
                respHdr.statusCode    = 0;
                respHdr.numDetections = 0; // Populated by client NMS or consumer
                respHdr.inferUs       = static_cast<uint32_t>(inferMs * 1000.0);
                respHdr.postprocUs    = 500; // <1ms
                respHdr.dataSize      = kawach::OUTPUT_SIZE * sizeof(float);

                if (!ipc.writeExact(&respHdr, sizeof(respHdr)) ||
                    !ipc.writeExact(outputBuffer.data(), respHdr.dataSize)) {
                    ipc.closeClient();
                    break;
                }
            } else {
                // Legacy response: [4-byte status] [output floats]
                uint32_t statusCode = 0;
                if (!ipc.writeExact(&statusCode, sizeof(statusCode)) ||
                    !ipc.writeExact(outputBuffer.data(), kawach::OUTPUT_SIZE * sizeof(float))) {
                    ipc.closeClient();
                    break;
                }
            }

            if (totalRequests % 100 == 0) {
                fprintf(stdout, "[kawach_worker] Stats: %lu total reqs (%lu ok, %lu failed), avg infer: %.2f ms (%.1f FPS)\n",
                        totalRequests, successRequests, failedRequests, totalInferMs / successRequests,
                        1000.0 / (totalInferMs / successRequests));
            }
        }
    }

    fprintf(stdout, "\n[kawach_worker] Daemon shutting down...\n");
    ipc.shutdown();

    if (successRequests > 0) {
        fprintf(stdout, "[kawach_worker] Final summary: %lu total requests served, %.2f ms avg HTP latency (%.1f FPS)\n",
                successRequests, totalInferMs / successRequests, 1000.0 / (totalInferMs / successRequests));
    }
    return 0;
}
