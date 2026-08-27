# 02. Setup and Target Access Guide

**Target Appliance:** `Kavach-EdgeBox` (Qualcomm QCS6490)  
**Host Tunneling:** Cloudflare Tunnel (`cloudflared`) over SSH  

---

## 1. Cloudflare Tunnel & SSH Configuration

### Step 1: Install `cloudflared`
Download the `cloudflared` binary for your platform and ensure it is available in your system `PATH`.

### Step 2: Configure `~/.ssh/config`
Append the dynamic routing block to your SSH configuration file:

```text
Host ssh.kavachx.io
    ProxyCommand cloudflared access ssh --hostname %h
    ServerAliveInterval 30
    ServerAliveCountMax 10
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new
```

### Step 3: Connect to Target Appliance
```bash
ssh work_user2@ssh.kavachx.io
```

---

## 2. Target Device Sanity & Group Permissions

Upon logging in, verify the user identity and groups:
```bash
whoami  # -> work_user2
pwd     # -> /home/work_user2
id      # -> uid=1006(work_user2) gid=1006(work_user2) groups=1006(work_user2),100(users),1005(qairt-users)
```

> [!IMPORTANT]
> **NPU Access Requirement (`render` Group):**  
> Direct access to `/dev/fastrpc-cdsp` and `/dev/dma_heap/system` requires membership in the `render` group. If `render` is absent from `id`, opening FastRPC sessions for the Hexagon DSP fails with `EACCES (14001)`. The account administrator must execute `sudo usermod -aG render work_user2`.

---

## 3. Remote Task Layout

The target appliance contains the following directory tree under `/home/work_user2/kawachx_task/`:
* `models/`: Source FP32 ONNX model (`new_3class_best_FP32.onnx`) and prior `.bin` artifacts (`3class_calibrated_final.bin`, `kawachx_aihub_split.bin`).
* `npu_worker/`: C++ inference daemon source files and `Makefile`.
* `test_images/`: Real test evaluation imagery (`fire.jpg`, `fire_2.jpg`, `person.jpg`).
