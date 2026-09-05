import asyncio
import json
import subprocess
import websockets

# Replace LAPTOP_IP with your laptop's IPv4 address (e.g. 192.168.29.69)
LAPTOP_IP = "192.168.29.69"
PORT = 8765
BROKER_URL = f"ws://{LAPTOP_IP}:{PORT}"


def handle_payload(payload: dict) -> dict:
    """Handles incoming action payloads from the laptop orchestrator."""
    if "status" in payload:
        return {}

    action = payload.get("action")
    url = payload.get("url") or payload.get("uri") or ""
    volume = payload.get("volume")
    print(f"[*] Received action: {action} | Payload: {payload}")

    # 1. Open URLs / Videos
    if action in ["OPEN_URL", "VIEW_VIDEO"] and url:
        print(f"[+] Launching URL on Android device: {url}")
        try:
            subprocess.run(["termux-open-url", url], check=True)
            return {"status": "success", "action": action, "url": url}
        except Exception:
            try:
                subprocess.run(["am", "start", "-a", "android.intent.action.VIEW", "-d", url], check=True)
                return {"status": "success", "action": action, "url": url}
            except Exception as err:
                return {"status": "error", "action": action, "error": str(err)}

    # 2. Hardware Android Volume Control via Keyevent Hardware Buttons
    elif action in ["SET_VOLUME", "MUTE", "UNMUTE", "MAX_VOLUME"]:
        target_vol = 0 if action == "MUTE" else (15 if action == "MAX_VOLUME" else (volume if volume is not None else 10))
        print(f"[+] Adjusting Android hardware volume to {target_vol}/15 via Keyevents...")

        if action == "MUTE" or target_vol == 0:
            # Press Volume Down 15 times
            for _ in range(15):
                subprocess.run(["input", "keyevent", "25"], check=False)
            print("[+] Phone Muted via Keyevent (Vol Down x15)")
            return {"status": "success", "action": action, "volume": 0}

        # Step 1: Zero out volume (Press Vol Down 15 times)
        for _ in range(15):
            subprocess.run(["input", "keyevent", "25"], check=False)

        # Step 2: Press Vol Up target_vol times
        for _ in range(target_vol):
            subprocess.run(["input", "keyevent", "24"], check=False)

        # Step 3: Try termux-volume as well
        try:
            subprocess.run(["termux-volume", "music", str(target_vol)], check=False)
        except Exception:
            pass

        print(f"[+] Real Android hardware volume set to {target_vol}/15!")
        return {"status": "success", "action": action, "volume": target_vol}

    # 3. Device Vibration
    elif action == "VIBRATE":
        duration = payload.get("duration", 500)
        print(f"[+] Triggering device vibration for {duration}ms...")
        try:
            subprocess.run(["termux-vibrate", "-d", str(duration)], check=True)
            return {"status": "success", "action": action}
        except Exception as e:
            return {"status": "error", "action": action, "error": str(e)}

    return {"status": "unknown_action", "action": action}


async def main():
    print(f"[*] Termux Mobile Listener connecting to laptop at {BROKER_URL}...")
    while True:
        try:
            async with websockets.connect(BROKER_URL) as ws:
                print("[+] Connected to laptop P2P Mesh Broker! Ready for video/sound commands...")
                async for message in ws:
                    try:
                        payload = json.loads(message)
                        result = handle_payload(payload)
                        if result:
                            await ws.send(json.dumps(result))
                    except json.JSONDecodeError:
                        print("[-] Received malformed payload.")
        except Exception as e:
            print(f"[!] Connection retry in 5s ({e})...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
