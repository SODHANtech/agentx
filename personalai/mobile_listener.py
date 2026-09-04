import asyncio
import json
import subprocess
import websockets

# Replace LAPTOP_IP with your laptop's IPv4 address (e.g. 192.168.1.100 or Tailscale IP)
LAPTOP_IP = "192.168.1.100"
PORT = 8765
BROKER_URL = f"ws://{LAPTOP_IP}:{PORT}"


def handle_payload(payload: dict) -> dict:
    """Handles incoming action payloads from the laptop orchestrator."""
    action = payload.get("action")
    url = payload.get("url") or payload.get("uri") or ""
    print(f"[*] Received action: {action} | URL: {url}")

    if action in ["OPEN_URL", "VIEW_VIDEO"] and url:
        print(f"[+] Launching URL on Android device: {url}")
        try:
            # Termux native intent handler
            subprocess.run(["termux-open-url", url], check=True)
            return {"status": "success", "action": action, "url": url}
        except Exception:
            # Android AM activity fallback
            try:
                subprocess.run(["am", "start", "-a", "android.intent.action.VIEW", "-d", url], check=True)
                return {"status": "success", "action": action, "url": url, "fallback": "am_start"}
            except Exception as err:
                return {"status": "error", "action": action, "error": str(err)}

    elif action == "VIBRATE":
        try:
            subprocess.run(["termux-vibrate", "-d", "500"], check=True)
            return {"status": "success", "action": action}
        except Exception as e:
            return {"status": "error", "action": action, "error": str(e)}

    return {"status": "unknown_action", "action": action}


async def main():
    print(f"[*] Termux Mobile Listener connecting to laptop at {BROKER_URL}...")
    while True:
        try:
            async with websockets.connect(BROKER_URL) as ws:
                print("[+] Connected to laptop P2P Mesh Broker! Ready for video/intent payloads...")
                async for message in ws:
                    try:
                        payload = json.loads(message)
                        result = handle_payload(payload)
                        await ws.send(json.dumps(result))
                    except json.JSONDecodeError:
                        print("[-] Received malformed payload.")
        except Exception as e:
            print(f"[!] Connection retry in 5s ({e})...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
