# Personal AI System (Zero-Leak, Cross-Platform, RAG & MCP)

A production-grade, zero-data-leak personal AI infrastructure operating entirely on local silicon, backed by Google Drive cold storage, local vector RAG, MCP tool matrix, and Tailscale P2P cross-platform automation.

---

## 🚀 Quick Start Guide

### 1. Installation
```powershell
cd e:\Agentx\personalai
pip install -e .
```

### 2. Check System Diagnostics
```powershell
python -m personalai.cli status
```

### 3. Interactive Zero-Leak AI Shell
```powershell
python -m personalai.cli chat
```

### 4. Ingest Documents into Local RAG Vector Store
```powershell
python -m personalai.cli ingest README.md
```

### 5. Start Cross-Platform P2P Mesh Broker
```powershell
python -m personalai.cli mesh-start
```

---

## 📱 Cross-Platform Mobile Automation Guide (Termux)

To open YouTube videos, launch web URLs, or control Android features from your laptop without any cloud servers:

### Step 1: Setup Termux on Android
1. Install **Termux** on your Android phone.
2. Run setup in Termux:
   ```bash
   pkg update && pkg upgrade -y
   pkg install python termux-api git -y
   pip install websockets
   ```

### Step 2: Start Mesh Broker on Laptop
Find your laptop's Wi-Fi IP address using `ipconfig` (e.g. `192.168.29.69`), then start the P2P Mesh Broker:
```powershell
python -m personalai.cli mesh-start
```

### Step 3: Create & Run Listener on Phone
In Termux on your phone, run:
```bash
cat << 'EOF' > listener.py
import asyncio, json, subprocess, websockets

LAPTOP_IP = "192.168.29.69"  # Replace with your laptop IPv4
BROKER_URL = f"ws://{LAPTOP_IP}:8765"

def handle_payload(payload):
    action = payload.get("action")
    url = payload.get("url") or payload.get("uri") or ""
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
                print("[+] Connected to Laptop Mesh! Ready for commands...")
                async for msg in ws:
                    res = handle_payload(json.loads(msg))
                    await ws.send(json.dumps(res))
        except Exception as e:
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
EOF
python listener.py
```

### Step 4: Trigger Video Playback from Laptop
Run the helper script on your laptop:
```powershell
python send_video.py
```

Your phone will instantly open YouTube and play the video!

---

## 🧪 Testing

Run the automated test suite:
```powershell
python -m unittest discover tests
```

---

## 📖 Complete Documentation
For the full end-to-end instruction manual, see [USER_GUIDE.md](USER_GUIDE.md).
