#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <chrono>
#include <dlfcn.h>

#include "QnnInterface.h"
#include "QnnBackend.h"
#include "QnnDevice.h"
#include "QnnContext.h"
#include "QnnGraph.h"
#include "QnnTensor.h"
#include "System/QnnSystemInterface.h"
#include "System/QnnSystemContext.h"

int main(int argc, char** argv) {
    if (argc < 4) {
        printf("Usage: %s <libQnnHtp.so> <libQnnSystem.so> <model.bin>\n", argv[0]);
        return 1;
    }
    const char* backendPath = argv[1];
    const char* systemPath  = argv[2];
    const char* modelPath   = argv[3];

    printf("=========================================\n");
    printf("  KavachX Step 7 — HTP Initialization Test\n");
    printf("=========================================\n");
    printf("Backend: %s\n", backendPath);
    printf("System:  %s\n", systemPath);
    printf("Model:   %s\n", modelPath);
    printf("-----------------------------------------\n");

    // 1. Load Backend Lib
    printf("[1] Loading Backend Library...\n");
    void* backendLib = dlopen(backendPath, RTLD_NOW | RTLD_LOCAL);
    if (!backendLib) {
        fprintf(stderr, "[FAIL] dlopen backend failed: %s\n", dlerror());
        return 1;
    }

    typedef Qnn_ErrorHandle_t (*GetProvidersFn)(const QnnInterface_t***, uint32_t*);
    auto getProviders = (GetProvidersFn)dlsym(backendLib, "QnnInterface_getProviders");
    if (!getProviders) {
        fprintf(stderr, "[FAIL] QnnInterface_getProviders not found: %s\n", dlerror());
        return 1;
    }
    const QnnInterface_t** providers = nullptr;
    uint32_t numProviders = 0;
    getProviders(&providers, &numProviders);
    QnnInterface_t qnnIf = *providers[0];

    // 2. Load System Lib
    printf("[2] Loading System Library...\n");
    void* systemLib = dlopen(systemPath, RTLD_NOW | RTLD_LOCAL);
    if (!systemLib) {
        fprintf(stderr, "[FAIL] dlopen system lib failed: %s\n", dlerror());
        return 1;
    }
    typedef Qnn_ErrorHandle_t (*GetSysProvidersFn)(const QnnSystemInterface_t***, uint32_t*);
    auto getSysProviders = (GetSysProvidersFn)dlsym(systemLib, "QnnSystemInterface_getProviders");
    if (!getSysProviders) {
        fprintf(stderr, "[FAIL] QnnSystemInterface_getProviders not found: %s\n", dlerror());
        return 1;
    }
    const QnnSystemInterface_t** sysProviders = nullptr;
    uint32_t numSysProviders = 0;
    getSysProviders(&sysProviders, &numSysProviders);
    QnnSystemInterface_t sysIf = *sysProviders[0];

    // 3. Create Backend
    printf("[3] Creating QNN Backend...\n");
    Qnn_BackendHandle_t backend = nullptr;
    Qnn_ErrorHandle_t err = qnnIf.QNN_INTERFACE_VER_NAME.backendCreate(nullptr, nullptr, &backend);
    if (err != QNN_SUCCESS) {
        fprintf(stderr, "[FAIL] backendCreate failed: %llu\n", (unsigned long long)err);
        return 1;
    }
    printf("    backendCreate: SUCCESS\n");

    // 4. Create HTP Device
    printf("[4] Creating Qualcomm Hexagon HTP Device...\n");
    auto devStart = std::chrono::steady_clock::now();
    Qnn_DeviceHandle_t device = nullptr;
    const QnnDevice_Config_t* devCfg[] = {nullptr};
    err = qnnIf.QNN_INTERFACE_VER_NAME.deviceCreate(nullptr, devCfg, &device);
    auto devEnd = std::chrono::steady_clock::now();
    double devMs = std::chrono::duration<double, std::milli>(devEnd - devStart).count();
    if (err != QNN_SUCCESS) {
        fprintf(stderr, "[FAIL] deviceCreate failed: %llu\n", (unsigned long long)err);
        return 1;
    }
    printf("    deviceCreate: SUCCESS (%.1f ms)\n", devMs);

    // 5. Read Binary File
    printf("[5] Reading Model Context Binary: %s...\n", modelPath);
    FILE* f = fopen(modelPath, "rb");
    if (!f) {
        fprintf(stderr, "[FAIL] Cannot open model binary: %s\n", modelPath);
        return 1;
    }
    fseek(f, 0, SEEK_END);
    size_t binSize = ftell(f);
    fseek(f, 0, SEEK_SET);
    void* binBuffer = malloc(binSize);
    if (fread(binBuffer, 1, binSize, f) != binSize) {
        fprintf(stderr, "[FAIL] fread failed\n");
        fclose(f);
        return 1;
    }
    fclose(f);
    printf("    Loaded %zu bytes (%f MB)\n", binSize, binSize / (1024.0 * 1024.0));

    // 6. Inspect Binary Info via System Interface
    printf("[6] Extracting Binary & Graph Metadata via QnnSystemContext...\n");
    QnnSystemContext_Handle_t sysCtx = nullptr;
    sysIf.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextCreate(&sysCtx);

    const QnnSystemContext_BinaryInfo_t* binInfo = nullptr;
    Qnn_ContextBinarySize_t binInfoSize = 0;
    err = sysIf.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextGetBinaryInfo(
        sysCtx, binBuffer, (Qnn_ContextBinarySize_t)binSize, &binInfo, &binInfoSize);
    if (err != QNN_SUCCESS || !binInfo) {
        fprintf(stderr, "[FAIL] systemContextGetBinaryInfo failed: %llu\n", (unsigned long long)err);
        return 1;
    }

    uint32_t numGraphs = 0;
    const QnnSystemContext_GraphInfo_t* graphs = nullptr;
    if (binInfo->version == QNN_SYSTEM_CONTEXT_BINARY_INFO_VERSION_1) {
        numGraphs = binInfo->contextBinaryInfoV1.numGraphs;
        graphs = binInfo->contextBinaryInfoV1.graphs;
    } else if (binInfo->version == QNN_SYSTEM_CONTEXT_BINARY_INFO_VERSION_2) {
        numGraphs = binInfo->contextBinaryInfoV2.numGraphs;
        graphs = binInfo->contextBinaryInfoV2.graphs;
    } else if (binInfo->version == QNN_SYSTEM_CONTEXT_BINARY_INFO_VERSION_3) {
        numGraphs = binInfo->contextBinaryInfoV3.numGraphs;
        graphs = binInfo->contextBinaryInfoV3.graphs;
    }

    printf("    BinaryInfo Version: %d, Graph Count: %u\n", (int)binInfo->version, numGraphs);
    if (numGraphs == 0 || !graphs) {
        fprintf(stderr, "[FAIL] No graphs found in binary\n");
        return 1;
    }

    const char* graphName = nullptr;
    uint32_t numInputs = 0, numOutputs = 0;
    Qnn_Tensor_t* inTensors = nullptr;
    Qnn_Tensor_t* outTensors = nullptr;

    if (graphs[0].version == QNN_SYSTEM_CONTEXT_GRAPH_INFO_VERSION_1) {
        graphName  = graphs[0].graphInfoV1.graphName;
        numInputs  = graphs[0].graphInfoV1.numGraphInputs;
        inTensors  = graphs[0].graphInfoV1.graphInputs;
        numOutputs = graphs[0].graphInfoV1.numGraphOutputs;
        outTensors = graphs[0].graphInfoV1.graphOutputs;
    } else if (graphs[0].version == QNN_SYSTEM_CONTEXT_GRAPH_INFO_VERSION_2) {
        graphName  = graphs[0].graphInfoV2.graphName;
        numInputs  = graphs[0].graphInfoV2.numGraphInputs;
        inTensors  = graphs[0].graphInfoV2.graphInputs;
        numOutputs = graphs[0].graphInfoV2.numGraphOutputs;
        outTensors = graphs[0].graphInfoV2.graphOutputs;
    } else if (graphs[0].version == QNN_SYSTEM_CONTEXT_GRAPH_INFO_VERSION_3) {
        graphName  = graphs[0].graphInfoV3.graphName;
        numInputs  = graphs[0].graphInfoV3.numGraphInputs;
        inTensors  = graphs[0].graphInfoV3.graphInputs;
        numOutputs = graphs[0].graphInfoV3.numGraphOutputs;
        outTensors = graphs[0].graphInfoV3.graphOutputs;
    }

    printf("    Graph[0] Name: '%s'\n", graphName ? graphName : "(null)");
    printf("    Inputs (%u):\n", numInputs);
    for (uint32_t i = 0; i < numInputs; ++i) {
        printf("      [%u] name='%s', dataType=%d, rank=%u, dims=[",
               i, inTensors[i].v1.name ? inTensors[i].v1.name : "", (int)inTensors[i].v1.dataType, inTensors[i].v1.rank);
        for (uint32_t d = 0; d < inTensors[i].v1.rank; ++d) {
            printf("%u%s", inTensors[i].v1.dimensions[d], d + 1 < inTensors[i].v1.rank ? "," : "");
        }
        printf("]\n");
    }

    printf("    Outputs (%u):\n", numOutputs);
    for (uint32_t i = 0; i < numOutputs; ++i) {
        printf("      [%u] name='%s', dataType=%d, rank=%u, dims=[",
               i, outTensors[i].v1.name ? outTensors[i].v1.name : "", (int)outTensors[i].v1.dataType, outTensors[i].v1.rank);
        for (uint32_t d = 0; d < outTensors[i].v1.rank; ++d) {
            printf("%u%s", outTensors[i].v1.dimensions[d], d + 1 < outTensors[i].v1.rank ? "," : "");
        }
        printf("]\n");
    }

    // 7. Create Context from Binary
    printf("[7] Creating Runtime Context on HTP from Binary...\n");
    auto ctxStart = std::chrono::steady_clock::now();
    Qnn_ContextHandle_t context = nullptr;
    const QnnContext_Config_t* ctxCfg[] = {nullptr};
    err = qnnIf.QNN_INTERFACE_VER_NAME.contextCreateFromBinary(
        backend, device, ctxCfg, binBuffer, (Qnn_ContextBinarySize_t)binSize, &context, nullptr);
    auto ctxEnd = std::chrono::steady_clock::now();
    double ctxMs = std::chrono::duration<double, std::milli>(ctxEnd - ctxStart).count();

    if (err != QNN_SUCCESS) {
        fprintf(stderr, "[FAIL] contextCreateFromBinary failed: %llu\n", (unsigned long long)err);
        return 1;
    }
    printf("    contextCreateFromBinary: SUCCESS (%.1f ms)\n", ctxMs);

    // 8. Retrieve Graph
    printf("[8] Retrieving Graph '%s'...\n", graphName);
    Qnn_GraphHandle_t graph = nullptr;
    err = qnnIf.QNN_INTERFACE_VER_NAME.graphRetrieve(context, graphName, &graph);
    if (err != QNN_SUCCESS) {
        fprintf(stderr, "[FAIL] graphRetrieve failed: %llu\n", (unsigned long long)err);
        return 1;
    }
    printf("    graphRetrieve: SUCCESS\n");

    // 9. Clean up
    sysIf.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextFree(sysCtx);
    qnnIf.QNN_INTERFACE_VER_NAME.contextFree(context, nullptr);
    qnnIf.QNN_INTERFACE_VER_NAME.deviceFree(device);
    qnnIf.QNN_INTERFACE_VER_NAME.backendFree(backend);
    free(binBuffer);
    dlclose(backendLib);
    dlclose(systemLib);

    printf("=========================================\n");
    printf("  HTP Initialization Test: ALL PASS\n");
    printf("=========================================\n");
    return 0;
}
