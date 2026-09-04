import hashlib
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from personalai.config import settings

logger = logging.getLogger(__name__)


class StorageSyncDaemon:
    """Manages cold-storage artifact synchronization between local SSD cache and Google Drive."""

    def __init__(self, cache_dir: Optional[Path] = None, remote_name: Optional[str] = None):
        self.cache_dir = cache_dir or settings.local_cache_dir
        self.remote_name = remote_name or settings.gdrive_remote_name
        settings.ensure_directories()

    def compute_sha256(self, file_path: Path) -> str:
        """Computes SHA-256 hash for a given file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def verify_local_artifacts(self) -> Dict[str, Dict[str, str]]:
        """Scans local SSD cache and computes hashes for base-models, adapters, and knowledge."""
        manifest = {}
        for category in ["base-models", "adapters", "knowledge"]:
            cat_dir = self.cache_dir / category
            manifest[category] = {}
            if cat_dir.exists():
                for item in cat_dir.glob("**/*"):
                    if item.is_file():
                        rel_path = item.relative_to(cat_dir).as_posix()
                        manifest[category][rel_path] = self.compute_sha256(item)
        return manifest

    def is_rclone_available(self) -> bool:
        """Checks if rclone binary is installed and accessible."""
        return shutil.which("rclone") is not None

    def sync_from_remote(self, category: str = "all") -> bool:
        """Syncs artifacts from Google Drive cold storage to local SSD cache using rclone."""
        if not self.is_rclone_available():
            logger.warning("rclone CLI not found. Falling back to local offline mode.")
            return False

        categories = ["base-models", "adapters", "knowledge"] if category == "all" else [category]
        success = True

        for cat in categories:
            remote_path = f"{self.remote_name}/{cat}"
            local_path = self.cache_dir / cat
            cmd = ["rclone", "sync", remote_path, str(local_path), "--update", "--checksum", "-v"]
            logger.info(f"Synchronizing {remote_path} -> {local_path}...")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info(f"Sync completed for {cat}: {result.stdout}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Sync failed for {cat}: {e.stderr}")
                success = False

        return success

    def sync_to_remote(self, category: str = "knowledge") -> bool:
        """Pushes updated local artifacts (e.g. encrypted RAG dumps/notes) to Google Drive."""
        if not self.is_rclone_available():
            logger.warning("rclone CLI not found. Cannot backup to cold storage.")
            return False

        remote_path = f"{self.remote_name}/{category}"
        local_path = self.cache_dir / category
        cmd = ["rclone", "sync", str(local_path), remote_path, "--update", "--checksum", "-v"]
        logger.info(f"Backing up {local_path} -> {remote_path}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Backup completed for {category}: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Backup failed for {category}: {e.stderr}")
            return False
