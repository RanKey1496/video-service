import asyncio
import nats
import json

async def main():
    try:
        nc = await nats.connect("nats://82.197.65.146:4222")

        #data = {"id": 1, "audio_path": "audio/1/6d93ae4f-4fa1-4047-8cc5-ae45ae02fbd7.wav", "media_path": ["video/1/DE7OulSuzEO.mp4","video/1/CAy0G2KHXgM.mp4","video/1/DE9z-y5uT5K.mp4"]}
        #await nc.publish("job.video.created", json.dumps(data).encode())
        
        data = {"id": 34, "status": "Prueba" }
        await nc.publish("job.video.result", json.dumps(data).encode())
        await nc.drain()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    asyncio.run(main())