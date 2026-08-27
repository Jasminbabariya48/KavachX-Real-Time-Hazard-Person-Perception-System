// qnn_inference.cpp
// -----------------
// Direct QNN C API integration with Hexagon v68 HTP execution and C++ vectorized DFL decoding.

#include "qnn_inference.hpp"

#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <cmath>
#include <algorithm>

using namespace kawach;

const char* kawach::statusString(Status s) {
    switch (s) {
        case Status::SUCCESS:              return "SUCCESS";
        case Status::ERROR_DLOPEN:         return "ERROR_DLOPEN";
        case Status::ERROR_INTERFACE_LOAD: return "ERROR_INTERFACE_LOAD";
        case Status::ERROR_BACKEND_CREATE: return "ERROR_BACKEND_CREATE";
        case Status::ERROR_DEVICE_CREATE:  return "ERROR_DEVICE_CREATE";
        case Status::ERROR_CONTEXT_CREATE: return "ERROR_CONTEXT_CREATE";
        case Status::ERROR_GRAPH_RETRIEVE: return "ERROR_GRAPH_RETRIEVE";
        case Status::ERROR_TENSOR_SETUP:   return "ERROR_TENSOR_SETUP";
        case Status::ERROR_INFER:          return "ERROR_INFER";
    }
    return "UNKNOWN";
}

static bool extractGraphs(const QnnSystemContext_BinaryInfo_t* bin,
                          const QnnSystemContext_GraphInfo_t** outGraphs,
                          uint32_t* outNumGraphs) {
    if (!bin || !outGraphs || !outNumGraphs) return false;
    switch (bin->version) {
        case QNN_SYSTEM_CONTEXT_BINARY_INFO_VERSION_1:
            *outGraphs    = bin->contextBinaryInfoV1.graphs;
            *outNumGraphs = bin->contextBinaryInfoV1.numGraphs;
            return true;
        case QNN_SYSTEM_CONTEXT_BINARY_INFO_VERSION_2:
            *outGraphs    = bin->contextBinaryInfoV2.graphs;
            *outNumGraphs = bin->contextBinaryInfoV2.numGraphs;
            return true;
        case QNN_SYSTEM_CONTEXT_BINARY_INFO_VERSION_3:
            *outGraphs    = bin->contextBinaryInfoV3.graphs;
            *outNumGraphs = bin->contextBinaryInfoV3.numGraphs;
            return true;
        default:
            return false;
    }
}

static bool extractGraph(const QnnSystemContext_GraphInfo_t* gi,
                         const char**         outName,
                         uint32_t*            outNumIn,
                         Qnn_Tensor_t**       outIn,
                         uint32_t*            outNumOut,
                         Qnn_Tensor_t**       outOut) {
    if (!gi) return false;
    switch (gi->version) {
        case QNN_SYSTEM_CONTEXT_GRAPH_INFO_VERSION_1:
            *outName   = gi->graphInfoV1.graphName;
            *outNumIn  = gi->graphInfoV1.numGraphInputs;
            *outIn     = gi->graphInfoV1.graphInputs;
            *outNumOut = gi->graphInfoV1.numGraphOutputs;
            *outOut    = gi->graphInfoV1.graphOutputs;
            return true;
        case QNN_SYSTEM_CONTEXT_GRAPH_INFO_VERSION_2:
            *outName   = gi->graphInfoV2.graphName;
            *outNumIn  = gi->graphInfoV2.numGraphInputs;
            *outIn     = gi->graphInfoV2.graphInputs;
            *outNumOut = gi->graphInfoV2.numGraphOutputs;
            *outOut    = gi->graphInfoV2.graphOutputs;
            return true;
        case QNN_SYSTEM_CONTEXT_GRAPH_INFO_VERSION_3:
            *outName   = gi->graphInfoV3.graphName;
            *outNumIn  = gi->graphInfoV3.numGraphInputs;
            *outIn     = gi->graphInfoV3.graphInputs;
            *outNumOut = gi->graphInfoV3.numGraphOutputs;
            *outOut    = gi->graphInfoV3.graphOutputs;
            return true;
        default:
            return false;
    }
}

QnnInference::~QnnInference() {
    shutdown();
}

Status QnnInference::initialize(const std::string& backendPath,
                                const std::string& systemLibPath,
                                const std::string& modelBinPath) {
    Status st;
    st = loadBackend(backendPath, systemLibPath);  if (st != Status::SUCCESS) return st;
    st = createBackend();                          if (st != Status::SUCCESS) return st;
    st = createDevice();                           if (st != Status::SUCCESS) return st;
    st = loadContextFromBinary(modelBinPath);      if (st != Status::SUCCESS) return st;
    st = retrieveGraph();                          if (st != Status::SUCCESS) return st;
    st = setupTensors();                           if (st != Status::SUCCESS) return st;

    // Precompute YOLOv8 8400 anchor grid
    m_anchorX.resize(8400);
    m_anchorY.resize(8400);
    m_stride.resize(8400);

    size_t idx = 0;
    int strides[3] = {8, 16, 32};
    int gridSizes[3] = {80, 40, 20};

    for (int s = 0; s < 3; ++s) {
        int g = gridSizes[s];
        int str = strides[s];
        for (int y = 0; y < g; ++y) {
            for (int x = 0; x < g; ++x) {
                m_anchorX[idx] = (float)x + 0.5f;
                m_anchorY[idx] = (float)y + 0.5f;
                m_stride[idx]  = (float)str;
                idx++;
            }
        }
    }

    m_initialized = true;
    return Status::SUCCESS;
}

void QnnInference::decodeDFL(const uint8_t* rawBbox, const uint8_t* rawCls, float* outTensor) {
    // outTensor is [1, 7, 8400] (shape: 7 * 8400 floats)
    // Row 0: cx, Row 1: cy, Row 2: w, Row 3: h, Row 4: cls0, Row 5: cls1, Row 6: cls2
    for (int a = 0; a < 8400; ++a) {
        // 1. Dequantize Class Scores
        for (int c = 0; c < 3; ++c) {
            uint8_t u = rawCls[c * 8400 + a];
            float s = ((float)((int32_t)u + m_clsOffset)) * m_clsScale;
            outTensor[(4 + c) * 8400 + a] = s;
        }

        // 2. DFL decode 4 coordinates
        float dist[4] = {0.0f, 0.0f, 0.0f, 0.0f};
        for (int coord = 0; coord < 4; ++coord) {
            float expSum = 0.0f;
            float expVals[16];
            float maxBin = -1e9f;

            for (int bin = 0; bin < 16; ++bin) {
                uint8_t u = rawBbox[(coord * 16 + bin) * 8400 + a];
                float val = ((float)((int32_t)u + m_bboxOffset)) * m_bboxScale;
                expVals[bin] = val;
                if (val > maxBin) maxBin = val;
            }
            for (int bin = 0; bin < 16; ++bin) {
                expVals[bin] = std::exp(expVals[bin] - maxBin);
                expSum += expVals[bin];
            }
            float weightedSum = 0.0f;
            for (int bin = 0; bin < 16; ++bin) {
                weightedSum += (expVals[bin] / expSum) * (float)bin;
            }
            dist[coord] = weightedSum;
        }

        float ax = m_anchorX[a];
        float ay = m_anchorY[a];
        float str = m_stride[a];

        float x1 = (ax - dist[0]) * str;
        float y1 = (ay - dist[1]) * str;
        float x2 = (ax + dist[2]) * str;
        float y2 = (ay + dist[3]) * str;

        float cx = (x1 + x2) * 0.5f;
        float cy = (y1 + y2) * 0.5f;
        float w  = (x2 - x1);
        float h  = (y2 - y1);

        outTensor[0 * 8400 + a] = cx;
        outTensor[1 * 8400 + a] = cy;
        outTensor[2 * 8400 + a] = w;
        outTensor[3 * 8400 + a] = h;
    }
}

Status QnnInference::infer(const uint8_t* inputData, float* outputData) {
    if (!m_initialized) return Status::ERROR_INFER;

    void* inputBuf = m_inputTensors[0].v1.clientBuf.data;
    if (!inputBuf) return Status::ERROR_INFER;
    std::memcpy(inputBuf, inputData, INPUT_SIZE * sizeof(uint8_t));

    Qnn_ErrorHandle_t err = m_qnnInterface.QNN_INTERFACE_VER_NAME.graphExecute(
        m_graph,
        m_inputTensors.data(),
        static_cast<uint32_t>(m_inputTensors.size()),
        m_outputTensors.data(),
        static_cast<uint32_t>(m_outputTensors.size()),
        nullptr,
        nullptr
    );
    if (err != QNN_SUCCESS) {
        fprintf(stderr, "[qnn] graphExecute failed: %llu\n", (unsigned long long)err);
        return Status::ERROR_INFER;
    }

    // Decode DFL directly into IPC outputData buffer [1, 7, 8400]
    decodeDFL(m_rawOutputBuffers[0].data(), m_rawOutputBuffers[1].data(), outputData);

    return Status::SUCCESS;
}

Status QnnInference::loadBackend(const std::string& backendPath,
                                 const std::string& systemLibPath) {
    m_backendLibHandle = dlopen(backendPath.c_str(), RTLD_NOW | RTLD_LOCAL);
    if (!m_backendLibHandle) return Status::ERROR_DLOPEN;

    m_systemLibHandle = dlopen(systemLibPath.c_str(), RTLD_NOW | RTLD_LOCAL);
    if (!m_systemLibHandle) return Status::ERROR_DLOPEN;

    typedef Qnn_ErrorHandle_t (*GetProvidersFn)(const QnnInterface_t***, uint32_t*);
    auto getProviders = reinterpret_cast<GetProvidersFn>(
        dlsym(m_backendLibHandle, "QnnInterface_getProviders"));
    if (!getProviders) return Status::ERROR_INTERFACE_LOAD;

    const QnnInterface_t** providers = nullptr;
    uint32_t numProviders = 0;
    if (getProviders(&providers, &numProviders) != QNN_SUCCESS || numProviders == 0) {
        return Status::ERROR_INTERFACE_LOAD;
    }
    m_qnnInterface = *providers[0];

    typedef Qnn_ErrorHandle_t (*GetSysProvidersFn)(const QnnSystemInterface_t***, uint32_t*);
    auto getSysProviders = reinterpret_cast<GetSysProvidersFn>(
        dlsym(m_systemLibHandle, "QnnSystemInterface_getProviders"));
    if (!getSysProviders) return Status::ERROR_INTERFACE_LOAD;

    const QnnSystemInterface_t** sysProviders = nullptr;
    uint32_t numSysProviders = 0;
    if (getSysProviders(&sysProviders, &numSysProviders) != QNN_SUCCESS || numSysProviders == 0) {
        return Status::ERROR_INTERFACE_LOAD;
    }
    m_sysInterface = *sysProviders[0];

    return Status::SUCCESS;
}

Status QnnInference::createBackend() {
    Qnn_ErrorHandle_t err = m_qnnInterface.QNN_INTERFACE_VER_NAME.backendCreate(
        nullptr, nullptr, &m_backend);
    if (err != QNN_SUCCESS) return Status::ERROR_BACKEND_CREATE;
    return Status::SUCCESS;
}

Status QnnInference::createDevice() {
    const QnnDevice_Config_t* deviceCfg[] = {nullptr};
    Qnn_ErrorHandle_t err = m_qnnInterface.QNN_INTERFACE_VER_NAME.deviceCreate(
        nullptr, deviceCfg, &m_device);
    if (err != QNN_SUCCESS) return Status::ERROR_DEVICE_CREATE;
    return Status::SUCCESS;
}

Status QnnInference::loadContextFromBinary(const std::string& modelBinPath) {
    FILE* f = fopen(modelBinPath.c_str(), "rb");
    if (!f) return Status::ERROR_CONTEXT_CREATE;
    fseek(f, 0, SEEK_END);
    size_t binSize = static_cast<size_t>(ftell(f));
    fseek(f, 0, SEEK_SET);

    void* binBuffer = malloc(binSize);
    if (!binBuffer) { fclose(f); return Status::ERROR_CONTEXT_CREATE; }
    size_t r = fread(binBuffer, 1, binSize, f);
    (void)r;
    fclose(f);

    QnnSystemContext_Handle_t sysCtx = nullptr;
    Qnn_ErrorHandle_t err = m_sysInterface.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextCreate(&sysCtx);
    if (err != QNN_SUCCESS) { free(binBuffer); return Status::ERROR_CONTEXT_CREATE; }

    const QnnSystemContext_BinaryInfo_t* binInfo = nullptr;
    Qnn_ContextBinarySize_t binInfoSize = 0;
    err = m_sysInterface.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextGetBinaryInfo(
        sysCtx, binBuffer, static_cast<Qnn_ContextBinarySize_t>(binSize),
        &binInfo, &binInfoSize);
    if (err != QNN_SUCCESS || !binInfo) {
        m_sysInterface.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextFree(sysCtx);
        free(binBuffer);
        return Status::ERROR_CONTEXT_CREATE;
    }

    const QnnSystemContext_GraphInfo_t* graphs = nullptr;
    uint32_t numGraphs = 0;
    if (!extractGraphs(binInfo, &graphs, &numGraphs) || numGraphs == 0) {
        m_sysInterface.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextFree(sysCtx);
        free(binBuffer);
        return Status::ERROR_CONTEXT_CREATE;
    }

    const char* gName = nullptr;
    uint32_t numIn = 0, numOut = 0;
    Qnn_Tensor_t* inT = nullptr;
    Qnn_Tensor_t* outT = nullptr;
    if (!extractGraph(&graphs[0], &gName, &numIn, &inT, &numOut, &outT)) {
        m_sysInterface.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextFree(sysCtx);
        free(binBuffer);
        return Status::ERROR_CONTEXT_CREATE;
    }

    m_graphName = gName;

    auto deepCopyTensors = [this](Qnn_Tensor_t* src, uint32_t n, std::vector<Qnn_Tensor_t>& dst) {
        dst.assign(src, src + n);
        for (uint32_t i = 0; i < n; ++i) {
            uint32_t rank = dst[i].v1.rank;
            if (rank > 0 && dst[i].v1.dimensions) {
                uint32_t* owned = (uint32_t*)malloc(rank * sizeof(uint32_t));
                memcpy(owned, dst[i].v1.dimensions, rank * sizeof(uint32_t));
                dst[i].v1.dimensions = owned;
                m_ownedDimensions.push_back(owned);
            }
        }
    };
    deepCopyTensors(inT, numIn, m_inputTensorTemplates);
    deepCopyTensors(outT, numOut, m_outputTensorTemplates);

    // Read quantization scale and offset
    if (numOut >= 2) {
        m_bboxScale  = outT[0].v1.quantizeParams.scaleOffsetEncoding.scale;
        m_bboxOffset = outT[0].v1.quantizeParams.scaleOffsetEncoding.offset;
        m_clsScale   = outT[1].v1.quantizeParams.scaleOffsetEncoding.scale;
        m_clsOffset  = outT[1].v1.quantizeParams.scaleOffsetEncoding.offset;
    }

    m_sysInterface.QNN_SYSTEM_INTERFACE_VER_NAME.systemContextFree(sysCtx);

    const QnnContext_Config_t* ctxCfg[] = {nullptr};
    err = m_qnnInterface.QNN_INTERFACE_VER_NAME.contextCreateFromBinary(
        m_backend, m_device, ctxCfg,
        binBuffer, static_cast<Qnn_ContextBinarySize_t>(binSize),
        &m_context, nullptr);
    free(binBuffer);

    if (err != QNN_SUCCESS) return Status::ERROR_CONTEXT_CREATE;
    return Status::SUCCESS;
}

Status QnnInference::retrieveGraph() {
    if (m_graphName.empty()) return Status::ERROR_GRAPH_RETRIEVE;
    Qnn_ErrorHandle_t err = m_qnnInterface.QNN_INTERFACE_VER_NAME.graphRetrieve(
        m_context, m_graphName.c_str(), &m_graph);
    if (err != QNN_SUCCESS) return Status::ERROR_GRAPH_RETRIEVE;
    return Status::SUCCESS;
}

Status QnnInference::setupTensors() {
    uint32_t numIn  = static_cast<uint32_t>(m_inputTensorTemplates.size());
    uint32_t numOut = static_cast<uint32_t>(m_outputTensorTemplates.size());

    m_inputTensors.assign(m_inputTensorTemplates.begin(), m_inputTensorTemplates.end());
    m_outputTensors.assign(m_outputTensorTemplates.begin(), m_outputTensorTemplates.end());
    m_rawOutputBuffers.resize(numOut);

    for (uint32_t i = 0; i < numIn; ++i) {
        size_t bufSize = INPUT_SIZE * sizeof(uint8_t);
        void* buf = malloc(bufSize);
        if (!buf) return Status::ERROR_TENSOR_SETUP;
        m_inputTensors[i].v1.memType            = QNN_TENSORMEMTYPE_RAW;
        m_inputTensors[i].v1.clientBuf.data     = buf;
        m_inputTensors[i].v1.clientBuf.dataSize = static_cast<uint32_t>(bufSize);
    }

    for (uint32_t i = 0; i < numOut; ++i) {
        size_t count = 1;
        for (uint32_t d = 0; d < m_outputTensorTemplates[i].v1.rank; ++d) {
            count *= m_outputTensorTemplates[i].v1.dimensions[d];
        }
        m_rawOutputBuffers[i].resize(count);
        m_outputTensors[i].v1.memType            = QNN_TENSORMEMTYPE_RAW;
        m_outputTensors[i].v1.clientBuf.data     = m_rawOutputBuffers[i].data();
        m_outputTensors[i].v1.clientBuf.dataSize = static_cast<uint32_t>(count);
    }

    return Status::SUCCESS;
}

void QnnInference::freeTensors() {
    for (auto& t : m_inputTensors) {
        if (t.v1.clientBuf.data) { free(t.v1.clientBuf.data); t.v1.clientBuf.data = nullptr; }
    }
    m_inputTensors.clear();
    m_outputTensors.clear();
    m_rawOutputBuffers.clear();
}

void QnnInference::shutdown() {
    if (!m_initialized && !m_backend) return;

    freeTensors();
    m_inputTensorTemplates.clear();
    m_outputTensorTemplates.clear();
    m_graphName.clear();

    for (auto* p : m_ownedDimensions) free(p);
    m_ownedDimensions.clear();
    for (auto* p : m_ownedDynamicDims) free(p);
    m_ownedDynamicDims.clear();

    if (m_context && m_qnnInterface.QNN_INTERFACE_VER_NAME.contextFree) {
        m_qnnInterface.QNN_INTERFACE_VER_NAME.contextFree(m_context, nullptr);
        m_context = nullptr;
    }
    if (m_device && m_qnnInterface.QNN_INTERFACE_VER_NAME.deviceFree) {
        m_qnnInterface.QNN_INTERFACE_VER_NAME.deviceFree(m_device);
        m_device = nullptr;
    }
    if (m_backend && m_qnnInterface.QNN_INTERFACE_VER_NAME.backendFree) {
        m_qnnInterface.QNN_INTERFACE_VER_NAME.backendFree(m_backend);
        m_backend = nullptr;
    }

    if (m_backendLibHandle) { dlclose(m_backendLibHandle); m_backendLibHandle = nullptr; }
    if (m_systemLibHandle)  { dlclose(m_systemLibHandle);  m_systemLibHandle  = nullptr; }

    m_initialized = false;
}