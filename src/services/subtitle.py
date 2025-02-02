import os
import srt
import assemblyai as aai
import srt_equalizer
from utils import print_info, print_error, print_success

class Subtitle:
    def __init__(self, key):
        aai.settings.api_key = key
        config = aai.TranscriptionConfig(language_code='es')
        self._transcriber = aai.Transcriber(config=config)
    
    def generate_subtitles(self, audio_path, output_folder):
        try:
            print_info("Generando subtitulos...")
            transcript = self._transcriber.transcribe(audio_path)
            subtitles = transcript.export_subtitles_srt()
            result_path_srt = os.path.join(output_folder, "subtitles.srt")
            result_path_ass = os.path.join(output_folder, "subtitles.ass")
            
            with open(result_path_srt, 'w', encoding='utf-8') as file:
                file.write(subtitles)
                
            self.equalize_subtitle(result_path_srt, 10)
            print_success(f"Subtitulos generados en {result_path_srt}")
            
            print_info("Convertiendo SRT a ASS...")
            self.convert_srt_to_ass(result_path_srt, result_path_ass)
            print_success(f"Subtitulos convertidos en {result_path_ass}")
            
            return result_path_srt, result_path_ass
        except Exception as e:
            print_error(f"Error generating subtitles: {e}")
            return None, None
        
    def equalize_subtitle(self, srt_path, max_chars=10):
        srt_equalizer.equalize_srt_file(srt_path, srt_path, max_chars)
        
    def convert_srt_to_ass(self, srt_path, result_path):
        with open(srt_path, 'r', encoding='utf-8') as file:
            srt_content = file.read()
            
        subtitles = list(srt.parse(srt_content))
        
        ass_header = """[Script Info]
Title: Converted from SRT
ScriptType: v4.00+
PlayResX: 384
PlayResY: 288
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,16,&Hffffff,&Hffffff,&H0,&H0,0,0,0,0,100,100,0,0,1,1,0,2,10,10,10,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        ass_subtitles = []
        for sub in subtitles:
            start = f"0:00:{sub.start.total_seconds():05.2f}".replace(".", ":")
            end = f"0:00:{sub.end.total_seconds():05.2f}".replace(".", ":")
            text = sub.content.replace("\n", "\\N")
            ass_subtitles.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")
        
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(ass_header)
            f.write("\n".join(ass_subtitles))