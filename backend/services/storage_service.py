import os
import shutil
from fastapi import UploadFile

class StorageService:
    @staticmethod
    def save_file(file: UploadFile, content: bytes, filename: str) -> str:
        # Prepare for Object Storage: This abstraction allows switching to S3 or GCS easily
        # For development, we store locally in backend/data/uploads/
        upload_dir = "backend/data/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Sanitize filename to prevent directory traversal
        clean_filename = os.path.basename(filename)
        file_path = os.path.join(upload_dir, clean_filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
            
        return file_path
