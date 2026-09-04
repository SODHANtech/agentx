import asyncio
import json
import websockets


async def main():
    uri = "ws://127.0.0.1:8765"
    video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    print(f"[*] Sending video launch request for {video_url} to P2P mesh...")

    async with websockets.connect(uri) as ws:
        payload = {
            "action": "OPEN_URL",
            "url": video_url,
        }
        await ws.send(json.dumps(payload))
        print("[+] Payload sent successfully across P2P Mesh!")


if __name__ == "__main__":
    asyncio.run(main())
