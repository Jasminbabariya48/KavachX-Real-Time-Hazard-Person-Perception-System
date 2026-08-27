#include <cstdio>
#include <cstdlib>
#include <cstring>
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
    if (argc < 4) return 1;
    const char* systemPath  = argv[2];
    const char* modelPath   = argv[3];

    void* systemLib = dlopen(systemPath, RTLD_NOW | RTLD_LOCAL);
    typedef Qnn_ErrorHandle_t (*GetSysProvidersFn)(const QnnSystemInterface_t***, uint32_t*);
    auto getSysProviders = (GetSysProvidersFn)dlsym(systemLib, "QnnSystemInterface_getProviders");
    const QnnSystemInterface_t** sysProviders = nullptr;
    uint32_t numSysProviders = 0;
    getSysProviders(&sysProviders, &numSysProviders);
    QnnSystemInterface_t sysIf = *sysProviders[0];

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
    uint32_t numInputs = graphs[0].graphInfoV3.numGraphInputs;
    uint32_t numOutputs = graphs[0].graphInfoV3.numGraphOutputs;
    Qnn_Tensor_t* inTensors = graphs[0].graphInfoV3.graphInputs;
    Qnn_Tensor_t* outTensors = graphs[0].graphInfoV3.graphOutputs;

    printf("=== MODEL QUANTIZATION ENCODINGS ===\n");
    for (uint32_t i = 0; i < numInputs; ++i) {
        auto& t = inTensors[i].v1;
        printf("Input[%u] '%s': dataType=0x%04X, def=%d, enc=%d\n", i, t.name, t.dataType, t.quantizeParams.encodingDefinition, t.quantizeParams.quantizationEncoding);
        printf("  scale: %e, offset: %d\n", t.quantizeParams.scaleOffsetEncoding.scale, t.quantizeParams.scaleOffsetEncoding.offset);
    }

    for (uint32_t i = 0; i < numOutputs; ++i) {
        auto& t = outTensors[i].v1;
        printf("Output[%u] '%s': dataType=0x%04X, def=%d, enc=%d, dims=[", i, t.name, t.dataType, t.quantizeParams.encodingDefinition, t.quantizeParams.quantizationEncoding);
        for (uint32_t d = 0; d < t.rank; ++d) printf("%u%s", t.dimensions[d], d + 1 < t.rank ? "," : "");
        printf("]\n");
        printf("  scale: %e, offset: %d\n", t.quantizeParams.scaleOffsetEncoding.scale, t.quantizeParams.scaleOffsetEncoding.offset);
    }

    sysIf.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextFree(sysCtx);
    free(binBuffer);
    dlclose(systemLib);
    return 0;
}
