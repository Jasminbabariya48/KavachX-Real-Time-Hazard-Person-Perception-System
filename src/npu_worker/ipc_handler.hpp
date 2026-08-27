/*
 * ipc_handler.hpp
 * ---------------
 * Hardened Unix domain socket IPC for Kawach NPU Worker.
 * Supports structured framing with Request IDs, latency metrics, and error codes,
 * while maintaining backward compatibility with fixed raw-buffer clients.
 */

#ifndef KAWACH_IPC_HANDLER_HPP
#define KAWACH_IPC_HANDLER_HPP

#include <cstdint>
#include <cstddef>
#include <string>
#include <sys/types.h>

namespace kawach {

// Protocol constants
constexpr uint32_t IPC_MAGIC_REQUEST  = 0x4B574158; // "KWAX"
constexpr uint32_t IPC_MAGIC_RESPONSE = 0x5841574B; // "XWAK"

constexpr size_t RAW_IMAGE_BYTES   = 1 * 3 * 640 * 640; // 1,228,800 bytes
constexpr size_t RAW_OUTPUT_FLOATS = 1 * 7 * 8400;      // 58,800 floats (235,200 bytes)

#pragma pack(push, 1)
struct IpcRequestHeader {
    uint32_t magic;         // IPC_MAGIC_REQUEST
    uint32_t requestId;     // Client-supplied monotonic request ID
    uint32_t payloadSize;   // Expected to be RAW_IMAGE_BYTES (1228800)
    uint32_t reserved;      // Flags / future expansion
};

struct IpcResponseHeader {
    uint32_t magic;         // IPC_MAGIC_RESPONSE
    uint32_t requestId;     // Matching request ID
    uint32_t statusCode;    // 0 = SUCCESS, 1 = INVALID_REQUEST, 2 = INFER_ERROR, 3 = TIMEOUT
    uint32_t numDetections; // Number of valid detections in response
    uint32_t inferUs;       // HTP execution time in microseconds
    uint32_t postprocUs;    // CPU DFL/NMS time in microseconds
    uint32_t dataSize;      // Size of payload following header (in bytes)
};
#pragma pack(pop)

class IpcHandler {
public:
    IpcHandler() = default;
    ~IpcHandler();

    IpcHandler(const IpcHandler&) = delete;
    IpcHandler& operator=(const IpcHandler&) = delete;

    bool listen(const std::string& socketPath);
    bool acceptClient(int timeoutMs = -1);
    ssize_t readExact(void* buffer, size_t size, int timeoutMs = 5000);
    bool writeExact(const void* buffer, size_t size);
    void closeClient();
    void shutdown();

    bool hasClient() const { return m_clientFd >= 0; }

private:
    int m_serverFd = -1;
    int m_clientFd = -1;
    std::string m_socketPath;
};

} // namespace kawach

#endif // KAWACH_IPC_HANDLER_HPP
