import os
import random
import ffmpeg
from uuid import uuid4
from utils import print_error, print_info, print_success

class Media:
    
    def __init__(self):
        pass
    
    def get_video_data(self, video_path):
        probe = ffmpeg.probe(video_path, v='error', select_streams='v:0', show_entries='stream=width,height,duration')

        width = probe['streams'][0]['width']
        height = probe['streams'][0]['height']
        duration = float(probe['streams'][0]['duration'])
        
        return width, height, duration
            
    def add_dark_overlay(self, video_path, clip, duration):
        width, height = 1080, 1920
        
        print_info(f"Anadiendo overlay negro de {width}x{height} a {video_path}")
        
        overlay = ffmpeg.input(f"color=black:s={width}x{height}", f="lavfi", t=duration) \
            .filter("format", "rgba") \
            .filter("colorchannelmixer", aa=0.5)
            
        clip = ffmpeg.overlay(clip, overlay)
        return clip
            
    def resize_and_crop_if_need(self, video_path, clip):
        width, height, duration = self.get_video_data(video_path)
        
        if (round((width/height), 4) < 0.5625):
            print_info(f"=> Redimensionando clip {video_path} a 1080x1920")
            clip.crop(x = width/2, y= height/2, width=width, height=round(width/0.5625))
        else:
            print_info(f"=> Redimensionando clip {video_path} a 1920x1080")
            clip.crop(x = width/2, y= height/2, width=round(0.5625*height), height=height)
            
        clip = clip.filter('scale', 1080, 1920)
        return clip

    def generate_random_clips_and_format(self, video_path, output_folder, num_clips=3, clip_duration=5, skip_start=2):
        print(video_path)
        if not os.path.exists(video_path):
            print_error(f"Error: El archivo {video_path} no existe.")
            return []
        
        try:
            width, height, duration = self.get_video_data(video_path)
            
            if clip_duration > (duration - skip_start):
                print_info("La duración del clip es mayor que la duración total del video, no se generarán clips")
                return []
            
            max_clips = int((duration - skip_start) // clip_duration)
            num_clips = min(num_clips, max_clips)
            
            if num_clips < 1:
                print_error("Error: No se pueden generar mclips con la configuración dada.")
                return []
            
            print_info(f"Generando {num_clips} clips aleatorios de {clip_duration} segundos cada uno...")
            
            os.makedirs(output_folder, exist_ok=True)
            
            clips_path = []
            
            for i in range(num_clips):
                start_time = random.uniform(skip_start, max(0, duration - clip_duration))
                end_time = start_time + clip_duration
                
                video_name = os.path.basename(video_path)
                file_path = os.path.join(output_folder, f"{video_name}_{i+1}_{start_time:.2f}_{end_time:.2f}.mp4")
                clip = ffmpeg.input(video_path, ss=start_time, t=clip_duration)
                clip = self.resize_and_crop_if_need(video_path, clip)
                clip = self.add_dark_overlay(video_path, clip, clip_duration)
                
                clip.output(file_path, loglevel='quiet').run(overwrite_output=True)
                clips_path.append(file_path)
                print_info(f"Clip {i+1} generado: {file_path}")
            
            return clips_path
        except Exception as e:
            print_error(f"Error al generar los clips: {e}")

            
    def combine(self, media_clips, audio_mixed_path, subtitles_path, result_folder):
        audio_data = ffmpeg.probe(audio_mixed_path)
        max_duration = float(audio_data['format']['duration'])
        print(max_duration)
        
        clips = []
        total_duration = 0
        
        while total_duration < max_duration:
            for video_path in media_clips:
                clip_data = ffmpeg.probe(video_path)
                video_stream = next((stream for stream in clip_data['streams'] if stream['codec_type'] == 'video'), None)
                
                if not video_stream:
                    raise ValueError(f"El archivo {video_path} no contiene un stream de video.")
                
                clip_duration = float(video_stream['duration'])
                #if total_duration + clip_duration > max_duration:
                #    break
                
                clips.append(ffmpeg.input(video_path))
                total_duration += clip_duration
                
                print_info(f"Clip {video_path} agregado: {total_duration} seg")
            #break
                
        if not clips:
            raise ValueError("No se encontraron clips para combinar.")

        try:
            output_path = os.path.join(result_folder, f"output_video.mp4")
            result_path = os.path.join(result_folder, f"result.mp4")
            
            print_info(f"Combinando {len(clips)} clips...")
            video_concat = ffmpeg.concat(*[clip.video for clip in clips], v=1, a=0)
            ffmpeg.output(video_concat.filter('subtitles', subtitles_path), output_path, loglevel='quiet').run(overwrite_output=True)
            print_success(f"Videos concatenados y subtitulos anadidos correctamente en: {output_path}")
            
            audio_clip = ffmpeg.input(audio_mixed_path).audio
            video_clip = ffmpeg.input(output_path).video

            print_info(f"Combinando audio y video...")
            ffmpeg.output(video_clip, audio_clip, result_path, codec='copy', loglevel='quiet').run(overwrite_output=True)
            print_success(f"Videos concatenados correctamente en: {result_path}")
            return output_path, result_path
        except ffmpeg._run.Error as e:
            print("FFmpeg error:", e)
            raise
    
    def mix_audios(self, audio_path, song_path, result_folder):
        audio_clip = ffmpeg.input(audio_path)
        song_clip = ffmpeg.input(song_path).filter('volume', 0.4)
        silence_clip_2_seconds = ffmpeg.input('anullsrc=r=44100:cl=stereo', f='lavfi', t=2)
        silence_clip_4_seconds = ffmpeg.input('anullsrc=r=44100:cl=stereo', f='lavfi', t=4)
        
        print_info("Mezclando audios y agregando silencios...")
        extended_audio = ffmpeg.concat(silence_clip_2_seconds, audio_clip, silence_clip_4_seconds, v=0, a=1)
        merged_audio = ffmpeg.filter([extended_audio, song_clip], 'amix', duration='shortest', dropout_transition=4)
        output_audio_path = os.path.join(result_folder, 'output_audio.mp3')
        ffmpeg.output(merged_audio, output_audio_path, loglevel='quiet').run(overwrite_output=True)
        print_success("Audios mezclados exitosamente.")
        return output_audio_path
    
    def choose_random_song(self, folder_path):
        print_info(f"Buscando canciones en la carpeta: {folder_path}")
        song_files = [f for f in os.listdir(folder_path) if f.endswith('.mp3')]
        if not song_files:
            raise Exception("No se encontraron canciones en la carpeta.")
        output_path = os.path.join(folder_path, random.choice(song_files))
        print_success(f"Canción elegida: {output_path}")
        return output_path