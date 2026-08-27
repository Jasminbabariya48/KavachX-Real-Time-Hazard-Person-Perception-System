# KavachX Technical Documentation Index

Welcome to the technical documentation for KavachX, an enterprise edge perception system powered by Qualcomm Hexagon v68 HTP DSP acceleration.

---

## 1. Architecture & Design
- [System Architecture](architecture/SYSTEM_ARCHITECTURE.md) — Comprehensive dataflow, NPU FastRPC transport, and DFL decoder design.

## 2. Deployment & Installation
- [Deployment Guide](deployment/DEPLOYMENT_GUIDE.md) — Pre-flight requirements, user permissions (`render` GID 993), and turnkey installation.
- [Camera Setup Guide](deployment/CAMERA_SETUP.md) — Configuration guide for V4L2 USB/CSI, RTSP IP streams, and video files.
- [Go-Live Guide](deployment/GO_LIVE_GUIDE.md) — Pre-commissioning validation and acceptance checklist.

## 3. Operations & Maintenance
- [Operations Runbook](operations/OPERATIONS_RUNBOOK.md) — Production service lifecycle commands (start, stop, restart, status).
- [Health & Monitoring](operations/HEALTH_AND_MONITORING.md) — Real-time health reporting specification (`/tmp/kawach_health.json`).
- [Troubleshooting Guide](operations/TROUBLESHOOTING.md) — Diagnostic checklists and recovery procedures.

## 4. Testing & Validation
- [Test Strategy](testing/TEST_STRATEGY.md) — Multi-tier testing approach across hardware, integration, and streaming.
- [Acceptance Tests](testing/ACCEPTANCE_TESTS.md) — Automated regression and functional acceptance suites.
- [Performance Testing](testing/PERFORMANCE_TESTING.md) — Latency, throughput, and hardware characterization.

## 5. Development & Contribution
- [Development Guide](development/DEVELOPMENT_GUIDE.md) — Local development workflow and environment setup.
- [Repository Architecture](development/REPOSITORY_ARCHITECTURE.md) — Codebase standards and directory ownership.
- [Contributing Guidelines](development/CONTRIBUTING.md) — Code style and PR workflow.

## 6. Handover & Status
- [Production Handover](handover/PRODUCTION_HANDOVER.md) — Deployment acceptance and platform specifications.
- [Project Status](handover/PROJECT_STATUS.md) — Operational status and DSP verification.
- [Repository Cleanup Report](handover/REPOSITORY_CLEANUP_REPORT.md) — Full refactoring and audit log.
