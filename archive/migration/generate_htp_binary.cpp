#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <dlfcn.h>

#include "QnnInterface.h"
#include "QnnBackend.h"
#include "QnnDevice.h"
#include "QnnContext.h"
#include "QnnGraph.h"
#include "QnnProperty.h"
#include "QnnWrapperUtils.hpp"

typedef Qnn_ErrorHandle_t (*ComposeGraphsFn)(
    Qnn_BackendHandle_t backend,
    QNN_INTERFACE_VER_TYPE qnnInterface,
    Qnn_ContextHandle_t context,
    const qnn_wrapper_api::GraphConfigInfo_t** graphConfigsInfo,
    uint32_t numGraphConfigsInfo,
    qnn_wrapper_api::GraphInfoPtr_t** graphsInfo,
    uint32_t* numGraphsInfo,
    bool debug,
    QnnLog_Callback_t logCallback,
    QnnLog_Level_t logLevel);

typedef Qnn_ErrorHandle_t (*FreeGraphsInfoFn)(
    qnn_wrapper_api::GraphInfoPtr_t** graphsInfo, uint32_t numGraphsInfo);

int main(int argc, char** argv) {
    if (argc < 4) {
        printf("Usage: %s <backend_so> <model_so> <output_bin>\n", argv[0]);
        return 1;
    }
    const char* backendPath = argv[1];
    const char* modelPath   = argv[2];
    const char* outputPath  = argv[3];

    printf("[1] Loading Backend: %s\n", backendPath);
    void* backendLib = dlopen(backendPath, RTLD_NOW | RTLD_GLOBAL);
    if (!backendLib) {
        fprintf(stderr, "dlopen backend failed: %s\n", dlerror());
        return 1;
    }

    typedef Qnn_ErrorHandle_t (*GetProvidersFn)(const QnnInterface_t***, uint32_t*);
    auto getProviders = (GetProvidersFn)dlsym(backendLib, "QnnInterface_getProviders");
    if (!getProviders) {
        fprintf(stderr, "QnnInterface_getProviders not found: %s\n", dlerror());
        return 1;
    }
    const QnnInterface_t** providers = nullptr;
    uint32_t numProviders = 0;
    getProviders(&providers, &numProviders);
    QnnInterface_t qnnIf = *providers[0];

    printf("[2] Creating Backend...\n");
    Qnn_BackendHandle_t backend = nullptr;
    qnnIf.QNN_INTERFACE_VER_NAME.backendCreate(nullptr, nullptr, &backend);

    printf("[3] Creating Device...\n");
    Qnn_DeviceHandle_t device = nullptr;
    const QnnDevice_Config_t* devCfg[] = {nullptr};
    Qnn_ErrorHandle_t err = qnnIf.QNN_INTERFACE_VER_NAME.deviceCreate(nullptr, devCfg, &device);
    if (err != QNN_SUCCESS) {
        fprintf(stderr, "deviceCreate failed: %llu\n", (unsigned long long)err);
        return 1;
    }

    printf("[4] Creating Context...\n");
    Qnn_ContextHandle_t context = nullptr;
    const QnnContext_Config_t* ctxCfg[] = {nullptr};
    err = qnnIf.QNN_INTERFACE_VER_NAME.contextCreate(backend, device, ctxCfg, &context);
    if (err != QNN_SUCCESS) {
        fprintf(stderr, "contextCreate failed: %llu\n", (unsigned long long)err);
        return 1;
    }

    printf("[5] Loading Model Shared Library: %s\n", modelPath);
    void* modelLib = dlopen(modelPath, RTLD_NOW | RTLD_GLOBAL);
    if (!modelLib) {
        fprintf(stderr, "dlopen modelLib failed: %s\n", dlerror());
        return 1;
    }

    auto composeGraphs = (ComposeGraphsFn)dlsym(modelLib, "QnnModel_composeGraphs");
    if (!composeGraphs) {
        fprintf(stderr, "QnnModel_composeGraphs not found: %s\n", dlerror());
        return 1;
    }

    printf("[6] Composing Graphs...\n");
    qnn_wrapper_api::GraphInfoPtr_t* graphsInfo = nullptr;
    uint32_t numGraphs = 0;
    err = composeGraphs(backend, qnnIf.QNN_INTERFACE_VER_NAME, context, nullptr, 0, &graphsInfo, &numGraphs, false, nullptr, QNN_LOG_LEVEL_INFO);
    if (err != QNN_SUCCESS || !graphsInfo || numGraphs == 0) {
        fprintf(stderr, "composeGraphs failed: %llu\n", (unsigned long long)err);
        return 1;
    }
    printf("ComposeGraphs succeeded! Found %u graph(s), Name: %s\n", numGraphs, graphsInfo[0]->graphName ? graphsInfo[0]->graphName : "(null)");

    printf("[7] Finalizing Graph...\n");
    Qnn_GraphHandle_t graphHandle = graphsInfo[0]->graph;
    err = qnnIf.QNN_INTERFACE_VER_NAME.graphFinalize(graphHandle, nullptr, nullptr);
    if (err != QNN_SUCCESS) {
        fprintf(stderr, "graphFinalize failed: %llu\n", (unsigned long long)err);
        return 1;
    }
    printf("Graph finalized on HTP!\n");

    printf("[8] Extracting Context Binary...\n");
    Qnn_ContextBinarySize_t binSize = 0;
    err = qnnIf.QNN_INTERFACE_VER_NAME.contextGetBinarySize(context, &binSize);
    if (err != QNN_SUCCESS) {
        fprintf(stderr, "contextGetBinarySize failed: %llu\n", (unsigned long long)err);
        return 1;
    }
    printf("Context Binary Size: %llu bytes (%f MB)\n", (unsigned long long)binSize, binSize / (1024.0 * 1024.0));

    void* binBuffer = malloc(binSize);
    Qnn_ContextBinarySize_t writtenSize = 0;
    err = qnnIf.QNN_INTERFACE_VER_NAME.contextGetBinary(context, binBuffer, binSize, &writtenSize);
    if (err != QNN_SUCCESS) {
        fprintf(stderr, "contextGetBinary failed: %llu\n", (unsigned long long)err);
        return 1;
    }

    printf("[9] Writing to %s (%llu bytes)...\n", outputPath, (unsigned long long)writtenSize);
    FILE* f = fopen(outputPath, "wb");
    if (!f) {
        fprintf(stderr, "Cannot open output file: %s\n", outputPath);
        return 1;
    }
    fwrite(binBuffer, 1, writtenSize, f);
    fclose(f);
    free(binBuffer);

    printf("SUCCESS! Context binary generated: %s\n", outputPath);
    return 0;
}
