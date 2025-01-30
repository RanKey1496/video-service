import os
import boto3
from utils import print_info, print_success, print_error

class S3:

    def __init__(self, region, access_key, secret_access_key):
        print_info("Initializing S3 client...")
        self._s3_client = boto3.client(
            service_name='s3',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_access_key
        )
        
        print_success("S3 client initialized.")
        
    def upload_file(self, file_path, bucket, key):
        try:
            print_info(f"Uploading file to S3: {file_path}")
            self._s3_client.upload_file(file_path, bucket, key)
            print_success(f"File uploaded to S3: {file_path}")
        except Exception as e:
            print_error(f"Error uploading file to S3: {e}")
            
    def upload_files(self, id, file_paths, bucket):
        keys = []
        for file_path in file_paths:
            filename = file_path.split("\\")[-1]
            key = f"result/{id}/{filename}"
            self.upload_file(file_path, bucket, key)
            keys.append(key)
        return keys
    
    def donwload_file(self, key_path, bucket, file_path):
        try:
            print_info(f"Downloading media from S3: {key_path}")
            self._s3_client.download_file(bucket, key_path, file_path)
            print_success(f"Media downloaded from S3: {key_path}")
        except Exception as e:
            print_error(f"Error downloading media from S3: {e}")
            
    def download_medias(self, media_paths, bucket, output):
        output_paths = []
        for media_path in media_paths:
            output_path = os.path.join(output, media_path.split("/")[-1])
            self.donwload_file(media_path, bucket, output_path)
            output_paths.append(output_path)
        return output_paths
            
    def download_audio(self, audio_path, bucket, output):
        output_path = os.path.join(output, audio_path.split("/")[-1])
        self.donwload_file(audio_path, bucket, output_path)
        return output_path
