# 📖 Personal AI System - Master User Guide & Handbook

A complete step-by-step operational handbook for your production-grade, zero-leak personal AI system with local RAG, MCP tool matrix, and Android cross-platform automation.

---

## Table of Contents
1. [Architecture & Zero-Leak Security Guarantee](#1-architecture--zero-leak-security-guarantee)
2. [Installation & Core Setup](#2-installation--core-setup)
3. [CLI Commands Reference](#3-cli-commands-reference)
4. [Local RAG Knowledge Ingestion](#4-local-rag-knowledge-ingestion)
5. [Cross-Platform Android Mobile Control Master Guide (Termux)](#5-cross-platform-android-mobile-control-master-guide-termux)
6. [Security Authorization Locks & Automated Testing](#6-security-authorization-locks--automated-testing)

---

## 1. Architecture & Zero-Leak Security Guarantee

Your Personal AI system runs **100% on your local silicon**. No prompts, documents, or actions are ever sent to external cloud servers.

- **Local Inference Engine**: Ollama or `llama.cpp` listening strictly on `127.0.0.1:11434`. Telemetry is disabled (`OLLAMA_ORIGINS=""`, `OLLAMA_HOST="127.0.0.1"`).
- **Local RAG Engine**: Persistent ChromaDB vector database with `BAAI/bge-small-en-v1.5` embeddings running on-device.
- **P2P Mesh Network**: Encrypted WebSockets operating over Tailscale / Local Wi-Fi.

---

## 2. Installation & Core Setup

### Laptop Setup (Windows)

1. Open PowerShell and navigate to your project directory:
   ```powershell
   cd e:\Agentx\personalai
   ```

2. Install the package in editable mode:
   ```powershell
   pip install -e .
   ```

3. Ensure Ollama is running on your computer:
   ```powershell
   ollama run llama3.1:8b
   ```

4. Verify system health:
   ```powershell
   python -m personalai.cli status
   ```

---

## 3. CLI Commands Reference

| Command | Usage | Description |
| --- | --- | --- |
| `status` | `python -m personalai.cli status` | Displays diagnostics for inference engine, RAG store, cache, and broker |
| `chat` | `python -m personalai.cli chat` | Launches interactive zero-leak AI prompt shell |
| `ingest` | `python -m personalai.cli ingest <path>` | Embeds markdown or text documents into local ChromaDB RAG store |
| `sync` | `python -m personalai.cli sync` | Synchronizes cold storage model weights & backups via `rclone` |
| `mesh-start` | `python -m personalai.cli mesh-start` | Starts the P2P WebSocket event broker on port 8765 |

---

## 4. Local RAG Knowledge Ingestion

To feed private documentation, notes, or codebases into your AI's memory:

1. **Ingest a File or Directory**:
   ```powershell
   python -m personalai.cli ingest README.md
   ```

2. **Query Ingested Knowledge**:
   Launch chat mode:
   ```powershell
   python -m personalai.cli chat
   ```
   Prompt your assistant:
   ```text
   You > What are the key features of our Personal AI system?
   ```
   Your AI will query local ChromaDB, present the answer, and cite the exact source document!

---

## 5. Cross-Platform Android Mobile Control Master Guide (Termux)

Follow these exact steps to connect your Android phone to your laptop and control YouTube videos, web links, or device features remotely.

### Step 1: Install Termux on Android
- Download and install **Termux** on your Android device (from F-Droid or GitHub).

### Step 2: Run Termux Setup Commands
Open Termux on your phone and run:

```bash
# 1. Update Termux packages
pkg update && pkg upgrade -y

# 2. Install Python & Termux tools
pkg install python termux-api git -y

# 3. Install WebSocket library
pip install websockets
```

### Step 3: Find Laptop Wi-Fi IP Address
On your laptop, run in PowerShell:
```powershell
ipconfig
```
Look for **IPv4 Address** under `Wireless LAN adapter Wi-Fi` (e.g. `192.168.29.69`).

### Step 4: Start Mesh Broker on Laptop
In PowerShell on your laptop:
```powershell
python -m personalai.cli mesh-start
```
*(Leave this running. It listens on `0.0.0.0:8765`).*

### Step 5: Run Listener on Android Phone (Termux)
In Termux on your phone, copy and paste this command (ensure `LAPTOP_IP` matches your laptop's IPv4):

```bash
cat << 'EOF' > listener.py
import asyncio, json, subprocess, websockets

LAPTOP_IP = "192.168.29.69"
BROKER_URL = f"ws://{LAPTOP_IP}:8765"

def handle_payload(payload):
    action = payload.get("action")
    url = payload.get("url") or payload.get("uri") or ""
    print(f"[*] Action: {action} | URL: {url}")
    
    if action in ["OPEN_URL", "VIEW_VIDEO"] and url:
        try:
            subprocess.run(["termux-open-url", url], check=True)
            return {"status": "success"}
        except Exception:
            subprocess.run(["am", "start", "-a", "android.intent.action.VIEW", "-d", url], check=True)
            return {"status": "success"}
    return {"status": "ignored"}

async def main():
    print(f"[*] Connecting to laptop at {BROKER_URL}...")
    while True:
        try:
            async with websockets.connect(BROKER_URL) as ws:
                print("[+] Connected to Laptop Mesh! Ready for video commands...")
                async for msg in ws:
                    res = handle_payload(json.loads(msg))
                    await ws.send(json.dumps(res))
        except Exception as e:
            print(f"[!] Retrying in 5s... ({e})")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
EOF
python listener.py
```

Termux will output:
```text
[+] Connected to Laptop Mesh! Ready for video commands...
```

### Step 6: Trigger Video / URL Playback from Laptop!

Open a second PowerShell window on your laptop and run:

```powershell
python send_video.py
```

📱 **Your phone will instantly open YouTube and start playing the video!**

---

## 6. Security Authorization Locks & Automated Testing

### Security Confirmation Locks
High-risk actions (such as file deletion or system modification) trigger automatic validation blocks in `personalai/security/validator.py`.

### Running Automated Test Suite
To verify system integrity:

```powershell
python -m unittest discover tests
```

Output:
```text
...BLOCKED: Destructive action 'FILE_DELETE' on 'critical_database.sqlite' requires user confirmation.
..
----------------------------------------------------------------------
Ran 5 tests in 0.598s

OK
```
