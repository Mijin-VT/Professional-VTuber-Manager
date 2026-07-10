"""Download manager with progress tracking, pause/resume, and SHA256 verification.
Handles GGUF model downloads from HuggingFace with a non-blocking UI approach.
"""

import hashlib
import os
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

import requests


class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DownloadTask:
    """Represents a single model download task."""
    model_id: str
    url: str
    sha256_url: str
    destination: Path
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    total_size: int = 0
    downloaded_bytes: int = 0
    error: str = ""
    paused: bool = False
    _cancel_requested: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock)
    progress_callback: Optional[Callable[..., None]] = None
    status_callback: Optional[Callable[[str], None]] = None


class DownloadManager:
    """Manages concurrent model downloads with pause/resume and verification."""

    def __init__(self, models_dir: str = "./models"):
        self._models_dir = Path(models_dir)
        self._models_dir.mkdir(parents=True, exist_ok=True)
        self._tasks: dict[str, DownloadTask] = {}
        self._threads: dict[str, threading.Thread] = {}

    def add_task(
        self,
        model_id: str,
        url: str,
        sha256_url: str,
        progress_callback: Optional[Callable[[float, int, int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        filename: str = "",
    ) -> DownloadTask:
        """Add a new download task."""
        # Use the actual GGUF filename if provided, otherwise use model_id
        if filename:
            dest = self._models_dir / filename
        else:
            dest = self._models_dir / f"{model_id}.gguf"
        task = DownloadTask(
            model_id=model_id,
            url=url,
            sha256_url=sha256_url,
            destination=dest,
            progress_callback=progress_callback,
            status_callback=status_callback,
        )
        self._tasks[model_id] = task
        return task

    def start_download(self, model_id: str) -> bool:
        """Start downloading a model in a background thread."""
        task = self._tasks.get(model_id)
        if not task:
            return False

        task.status = DownloadStatus.DOWNLOADING
        task._cancel_requested = False
        task.paused = False

        thread = threading.Thread(
            target=self._download_worker, args=(task,), daemon=True
        )
        self._threads[model_id] = thread
        thread.start()
        return True

    def pause_download(self, model_id: str) -> bool:
        """Pause a running download."""
        task = self._tasks.get(model_id)
        if not task or task.status != DownloadStatus.DOWNLOADING:
            return False
        task.paused = True
        task.status = DownloadStatus.PAUSED
        return True

    def resume_download(self, model_id: str) -> bool:
        """Resume a paused download."""
        task = self._tasks.get(model_id)
        if not task or task.status != DownloadStatus.PAUSED:
            return False
        task.paused = False
        task.status = DownloadStatus.DOWNLOADING

        thread = threading.Thread(
            target=self._download_worker, args=(task,), daemon=True
        )
        self._threads[model_id] = thread
        thread.start()
        return True

    def cancel_download(self, model_id: str) -> bool:
        """Cancel a running or paused download."""
        task = self._tasks.get(model_id)
        if not task:
            return False
        with task._lock:
            task._cancel_requested = True
        task.paused = True
        task.status = DownloadStatus.FAILED
        task.error = "Cancelled by user"
        # Clean up partial and destination files
        part_dest = task.destination.with_suffix(task.destination.suffix + ".part")
        if part_dest.exists():
            try:
                part_dest.unlink()
            except Exception:
                pass
        if task.destination.exists():
            try:
                task.destination.unlink()
            except Exception:
                pass
        return True

    def get_task(self, model_id: str) -> Optional[DownloadTask]:
        """Get download task by model ID."""
        return self._tasks.get(model_id)

    def is_complete(self, model_id: str) -> bool:
        """Check if a model download is complete."""
        task = self._tasks.get(model_id)
        if not task:
            return False
        return task.status == DownloadStatus.COMPLETED

    def delete_model(self, model_id: str) -> bool:
        """Delete a downloaded model file."""
        task = self._tasks.get(model_id)
        if not task:
            return False
        part_dest = task.destination.with_suffix(task.destination.suffix + ".part")
        if part_dest.exists():
            try:
                part_dest.unlink()
            except Exception:
                pass
        if task.destination.exists():
            try:
                task.destination.unlink()
            except Exception:
                pass
        task.status = DownloadStatus.PENDING
        task.progress = 0.0
        task.downloaded_bytes = 0
        task.error = ""
        task.paused = False
        task._cancel_requested = False
        return True

    def _download_worker(self, task: DownloadTask) -> None:
        """Worker thread that performs the actual download."""
        import time
        start_time = time.time()
        start_bytes = task.downloaded_bytes
        try:
            # If the final file already exists, it is complete and verified
            if task.destination.exists():
                task.total_size = task.destination.stat().st_size
                task.downloaded_bytes = task.total_size
                task.progress = 1.0
                task.status = DownloadStatus.COMPLETED
                if task.status_callback:
                    task.status_callback("completed")
                return

            part_destination = task.destination.with_suffix(task.destination.suffix + ".part")

            # Check if we are resuming from a part file on disk
            if part_destination.exists():
                part_size = part_destination.stat().st_size
                if task.downloaded_bytes == 0:
                    task.downloaded_bytes = part_size
                    start_bytes = part_size
            else:
                task.downloaded_bytes = 0
                start_bytes = 0

            # Download with streaming support
            headers = {}
            if task.downloaded_bytes > 0:
                headers["Range"] = f"bytes={task.downloaded_bytes}-"

            response = requests.get(
                task.url,
                stream=True,
                headers=headers,
                timeout=30,
            )
            
            # If server doesn't support Range requests or returns 200 instead of 206, reset download
            if response.status_code == 200 and task.downloaded_bytes > 0:
                task.downloaded_bytes = 0
                start_bytes = 0
                # Truncate part file
                with open(part_destination, "wb") as f:
                    pass
            else:
                response.raise_for_status()

            # Get total size
            if task.total_size == 0:
                content_range = response.headers.get("Content-Range")
                if content_range:
                    task.total_size = int(content_range.split("/")[-1])
                else:
                    cl = int(response.headers.get("Content-Length", 0))
                    task.total_size = cl + task.downloaded_bytes

            # Write in chunks to the part file
            write_mode = "ab" if task.downloaded_bytes > 0 else "wb"
            with open(part_destination, write_mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    with task._lock:
                        if task._cancel_requested:
                            return
                        if task.paused:
                            break

                    if chunk:
                        f.write(chunk)
                        task.downloaded_bytes += len(chunk)
                        if task.total_size > 0:
                            task.progress = min(
                                task.downloaded_bytes / task.total_size, 1.0
                            )

                        # Calcular métricas de velocidad y ETA
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0.1:
                            bytes_downloaded_in_session = task.downloaded_bytes - start_bytes
                            speed_bps = bytes_downloaded_in_session / elapsed_time
                            speed_mbps = speed_bps / (1024 * 1024)
                            
                            remaining_bytes = task.total_size - task.downloaded_bytes
                            if speed_bps > 0:
                                eta_seconds = remaining_bytes / speed_bps
                                if eta_seconds > 3600:
                                    hours = int(eta_seconds // 3600)
                                    mins = int((eta_seconds % 3600) // 60)
                                    secs = int(eta_seconds % 60)
                                    eta_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
                                else:
                                    mins = int(eta_seconds // 60)
                                    secs = int(eta_seconds % 60)
                                    eta_str = f"{mins:02d}:{secs:02d}"
                            else:
                                eta_str = "--:--"
                        else:
                            speed_mbps = 0.0
                            eta_str = "Calculando..."

                        if task.progress_callback:
                            task.progress_callback(
                                task.progress,
                                task.downloaded_bytes,
                                task.total_size,
                                speed_mbps,
                                eta_str,
                            )

            if task.paused:
                return

            # Verify SHA256 on the part file
            if task.status_callback:
                task.status_callback("verifying")
            self._verify_sha256(task, part_destination)

        except Exception as e:
            task.status = DownloadStatus.FAILED
            task.error = str(e)
            if task.status_callback:
                task.status_callback("failed")

    def _verify_sha256(self, task: DownloadTask, file_path: Optional[Path] = None) -> None:
        """Verify downloaded file against SHA256 checksum."""
        if file_path is None:
            file_path = task.destination

        if not file_path.exists():
            task.status = DownloadStatus.FAILED
            task.error = "File not found after download"
            return

        # Try to download .sha256 file first
        sha256_expected = None
        if task.sha256_url:
            try:
                resp = requests.get(task.sha256_url, timeout=10)
                if resp.status_code == 200:
                    sha256_expected = resp.text.strip().split()[0].lower()
            except Exception:
                pass  # Continue with local verification

        # Compute local SHA256
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
        computed = sha256_hash.hexdigest().lower()

        if sha256_expected and computed != sha256_expected:
            task.status = DownloadStatus.FAILED
            task.error = (
                f"SHA256 mismatch: expected {sha256_expected}, "
                f"got {computed}"
            )
            try:
                file_path.unlink(missing_ok=True)
            except Exception:
                pass
            return

        # Rename part file to final destination if we verified the part file
        if file_path != task.destination:
            try:
                if task.destination.exists():
                    task.destination.unlink()
                file_path.rename(task.destination)
            except Exception as e:
                task.status = DownloadStatus.FAILED
                task.error = f"Failed to rename verified file: {e}"
                return

        task.status = DownloadStatus.COMPLETED
        task.progress = 1.0
        if task.status_callback:
            task.status_callback("completed")
