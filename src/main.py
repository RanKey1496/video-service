import os
import asyncio
import utils
import json
import shutil
import time
from services.s3 import S3
from services.nat import Broker
from services.media import Media
from services.subtitle import Subtitle
from config import (get_nats_url, get_s3_region, get_s3_bucket, get_s3_key, get_s3_secret, get_assemblyai_api_key)

class Main:
    
    def __init__(self):
        self._s3 = S3(get_s3_region(), get_s3_key(), get_s3_secret())
        self._nats = Broker()
        self._subtitle = Subtitle(get_assemblyai_api_key())
        self._media = Media()
    
    async def job_video_created_handler(self, msg):
        utils.print_info(f"Received a message on '{msg.subject}': {msg.data.decode()}")
        start = time.time()
        data = json.loads(msg.data.decode())
        
        output_folder = os.path.join("media", str(data["id"]))
        os.makedirs(output_folder, exist_ok=True)
        
        audio_path = self._s3.download_audio(data["audio_path"], get_s3_bucket(), output_folder)
        #self._media.speed_up_audio(audio_path)
        
        media_path = self._s3.download_medias(data["media_path"], get_s3_bucket(), output_folder)
        
        clips_path = []
        
        await self._nats.publish("job.video.result", json.dumps({ "id": int(data["id"]), "status": "Creando clips" }).encode())
        for i in range(len(media_path)):
            output_clip = self._media.generate_random_clips_and_format(media_path[i], output_folder, 4, 5, 1)
            clips_path.extend(output_clip)
        
        result_folder = os.path.join("result", str(data["id"]))
        os.makedirs(result_folder, exist_ok=True)
        song_path = self._media.choose_random_song('songs')
        
        await self._nats.publish("job.video.result", json.dumps({ "id": int(data["id"]), "status": "Mezclando audios" }).encode())
        audio_mixed_path = self._media.mix_audios(audio_path, song_path, result_folder)
        subtitles_path_srt, subtitles_path_ass = self._subtitle.generate_subtitles(audio_mixed_path, result_folder)
        
        await self._nats.publish("job.video.result", json.dumps({ "id": int(data["id"]), "status": "Combinando audio y video" }).encode())
        output_path, result_path = self._media.combine(clips_path, audio_mixed_path, subtitles_path_ass, result_folder)
        
        # Eliminar los archivos utilizados para generar el código final
        [shutil.rmtree(os.path.dirname(file)) for file in [audio_path] + media_path if os.path.exists(file)]
        
        self._s3.upload_files(data['id'], [audio_mixed_path, subtitles_path_srt, subtitles_path_ass, output_path, result_path], get_s3_bucket())
        await self._nats.publish("job.video.finished", json.dumps({ "id": int(data["id"]), "result": result_path }).encode())
        
        # Eliminar todos los archivos generados
        [shutil.rmtree(os.path.dirname(file)) for file in [audio_mixed_path, subtitles_path_srt, subtitles_path_ass, output_path, result_path]  if os.path.exists(file)]
        end = time.time()
        utils.print_success(f"Processing time: {end - start}")
    
    async def run(self):
        await self._nats.connect(get_nats_url())
        await self._nats.subscribe("job.video.created", self.job_video_created_handler)
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    main_app = Main()
    try:
        loop.run_until_complete(main_app.run())
    except KeyboardInterrupt:
        print("Shutting down...")