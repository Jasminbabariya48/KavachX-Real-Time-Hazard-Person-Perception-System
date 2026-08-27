// qnn_inference.hpp
// -----------------
// QNN C-API lifecycle wrapper for kawach_worker.
// Manages one persistent HTP context: init once, infer forever.

#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <cstdio>
#include <dlfcn.h>

// QNN public headers
#include "QnnInterface.h"
#include "QnnTypes.h"
#include "QnnBackend.h"
#include "QnnContext.h"
#include "QnnGraph.h"
#include "QnnTensor.h"
#include "HTP/QnnHtpDevice.h"
#include "System/QnnSystemInterface.h"
#include "System/QnnSystemContext.h"

namespace kawach {

enum class Status {
    SUCCESS = 0,
    ERROR_DLOPEN,
    ERROR_INTERFACE_LOAD,
    ERROR_BACKEND_CREATE,
    ERROR_DEVICE_CREATE,
    ERROR_CONTEXT_CREATE,
    ERROR_GRAPH_RETRIEVE,
    ERROR_TENSOR_SETUP,
    ERROR_INFER,
};

const char* statusString(Status s);

// Fixed model I/O dimensions
static constexpr uint32_t INPUT_SIZE  = 1u * 3u * 640u * 640u; // uint8, NCHW
static constexpr uint32_t OUTPUT_SIZE = 1u * 7u * 8400u;       // float32 count (1,7,8400)

class QnnInference {
public:
    QnnInference() = default;
    ~QnnInference();

    QnnInference(const QnnInference&)            = delete;
    QnnInference& operator=(const QnnInference&) = delete;

    Status initialize(const std::string& backendPath,
                      const std::string& systemLibPath,
                      const std::string& modelBinPath);

    Status infer(const uint8_t* inputData, float* outputData);

    bool isInitialized() const { return m_initialized; }

private:
    Status loadBackend(const std::string& backendPath, const std::string& systemLibPath);
    Status createBackend();
    Status createDevice();
    Status loadContextFromBinary(const std::string& modelBinPath);
    Status retrieveGraph();
    Status setupTensors();

    void decodeDFL(const uint8_t* rawBbox, const uint8_t* rawCls, float* outTensor);
    void freeTensors();
    void shutdown();

    void* m_backendLibHandle = nullptr;
    void* m_systemLibHandle  = nullptr;

    QnnInterface_t       m_qnnInterface = {};
    QnnSystemInterface_t m_sysInterface = {};

    Qnn_BackendHandle_t  m_backend = nullptr;
    Qnn_DeviceHandle_t   m_device  = nullptr;
    Qnn_ContextHandle_t  m_context = nullptr;
    Qnn_GraphHandle_t    m_graph   = nullptr;

    std::string                m_graphName;
    std::vector<Qnn_Tensor_t>  m_inputTensorTemplates;
    std::vector<Qnn_Tensor_t>  m_outputTensorTemplates;

    std::vector<uint32_t*>     m_ownedDimensions;
    std::vector<uint8_t*>      m_ownedDynamicDims;

    std::vector<Qnn_Tensor_t>  m_inputTensors;
    std::vector<Qnn_Tensor_t>  m_outputTensors;
    std::vector<std::vector<uint8_t>> m_rawOutputBuffers;

    float   m_bboxScale  = 0.1574602f;
    int32_t m_bboxOffset = -191;
    float   m_clsScale   = 0.00390625f;
    int32_t m_clsOffset  = 0;

    std::vector<float> m_anchorX;
    std::vector<float> m_anchorY;
    std::vector<float> m_stride;

    bool m_initialized = false;
};

} // namespace kawach