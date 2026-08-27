/*
 * ipc_handler.cpp
 * ---------------
 * Robust Unix Domain Socket IPC Implementation with timeout and error handling.
 */

#include "ipc_handler.hpp"

#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <poll.h>
#include <fcntl.h>
#include <cerrno>
#include <cstring>
#include <cstdio>

using namespace kawach;

IpcHandler::~IpcHandler() {
    shutdown();
}

bool IpcHandler::listen(const std::string& socketPath) {
    shutdown();
    m_socketPath = socketPath;

    // Unlink any stale socket file
    unlink(m_socketPath.c_str());

    m_serverFd = ::socket(AF_UNIX, SOCK_STREAM, 0);
    if (m_serverFd < 0) {
        fprintf(stderr, "[ipc] socket() failed: %s\n", strerror(errno));
        return false;
    }

    // Set non-blocking or close-on-exec
    int flags = fcntl(m_serverFd, F_GETFD, 0);
    if (flags >= 0) fcntl(m_serverFd, F_SETFD, flags | FD_CLOEXEC);

    struct sockaddr_un addr;
    std::memset(&addr, 0, sizeof(addr));
    addr.sun_family = AF_UNIX;
    std::strncpy(addr.sun_path, m_socketPath.c_str(), sizeof(addr.sun_path) - 1);

    if (::bind(m_serverFd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        fprintf(stderr, "[ipc] bind(\"%s\") failed: %s\n", m_socketPath.c_str(), strerror(errno));
        close(m_serverFd);
        m_serverFd = -1;
        return false;
    }

    if (::listen(m_serverFd, 16) < 0) {
        fprintf(stderr, "[ipc] listen() failed: %s\n", strerror(errno));
        close(m_serverFd);
        m_serverFd = -1;
        return false;
    }

    fprintf(stdout, "[ipc] Listening on Unix socket: %s\n", m_socketPath.c_str());
    return true;
}

bool IpcHandler::acceptClient(int timeoutMs) {
    if (m_serverFd < 0) return false;
    closeClient();

    if (timeoutMs >= 0) {
        struct pollfd pfd;
        pfd.fd = m_serverFd;
        pfd.events = POLLIN;
        pfd.revents = 0;
        int ret = poll(&pfd, 1, timeoutMs);
        if (ret <= 0) return false;
    }

    m_clientFd = ::accept(m_serverFd, nullptr, nullptr);
    if (m_clientFd < 0) {
        if (errno != EINTR && errno != EAGAIN) {
            fprintf(stderr, "[ipc] accept() error: %s\n", strerror(errno));
        }
        return false;
    }

    int flags = fcntl(m_clientFd, F_GETFD, 0);
    if (flags >= 0) fcntl(m_clientFd, F_SETFD, flags | FD_CLOEXEC);

    return true;
}

ssize_t IpcHandler::readExact(void* buffer, size_t size, int timeoutMs) {
    if (m_clientFd < 0) return -1;

    uint8_t* ptr = static_cast<uint8_t*>(buffer);
    size_t totalRead = 0;

    while (totalRead < size) {
        if (timeoutMs > 0) {
            struct pollfd pfd;
            pfd.fd = m_clientFd;
            pfd.events = POLLIN;
            pfd.revents = 0;
            int ret = poll(&pfd, 1, timeoutMs);
            if (ret == 0) {
                fprintf(stderr, "[ipc] read timeout (%d ms)\n", timeoutMs);
                return -2; // Timeout
            }
            if (ret < 0) {
                if (errno == EINTR) continue;
                return -1;
            }
        }

        ssize_t n = ::read(m_clientFd, ptr + totalRead, size - totalRead);
        if (n == 0) {
            // EOF: Client closed socket
            return totalRead == 0 ? 0 : -1;
        }
        if (n < 0) {
            if (errno == EINTR) continue;
            if (errno == EAGAIN || errno == EWOULDBLOCK) continue;
            return -1;
        }
        totalRead += static_cast<size_t>(n);
    }
    return static_cast<ssize_t>(totalRead);
}

bool IpcHandler::writeExact(const void* buffer, size_t size) {
    if (m_clientFd < 0) return false;

    const uint8_t* ptr = static_cast<const uint8_t*>(buffer);
    size_t totalWritten = 0;

    while (totalWritten < size) {
        ssize_t n = ::write(m_clientFd, ptr + totalWritten, size - totalWritten);
        if (n <= 0) {
            if (n < 0 && (errno == EINTR || errno == EAGAIN)) continue;
            return false;
        }
        totalWritten += static_cast<size_t>(n);
    }
    return true;
}

void IpcHandler::closeClient() {
    if (m_clientFd >= 0) {
        ::close(m_clientFd);
        m_clientFd = -1;
    }
}

void IpcHandler::shutdown() {
    closeClient();
    if (m_serverFd >= 0) {
        ::close(m_serverFd);
        m_serverFd = -1;
    }
    if (!m_socketPath.empty()) {
        unlink(m_socketPath.c_str());
        m_socketPath.clear();
    }
}
