import pika
import json
import logging
import time
from datetime import datetime
import os
from dataclasses import dataclass
import signal
import requests
from PIL import Image
from io import BytesIO
import tempfile
from typing import Optional, Tuple, Dict, Any
from enum import Enum
import threading
from task_processor import TaskProcessor, TaskConsumer, Config


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class ProcessingResult:
    status: ProcessingStatus
    message: str
    retry_count: int
    processing_time: float
    result_data: Optional[Dict] = None
    error: Optional[Exception] = None


@dataclass
class ImageProcessingConfig(Config):
    thumbnail_size: Tuple[int, int] = (200, 200)
    quality: int = 85
    format: str = "JPEG"


class ImageProcessor(TaskProcessor):
    """Handles image processing operations"""

    def __init__(self, config: ImageProcessingConfig):
        super().__init__()
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "ImageProcessor/1.0",
                "Authorization": f"Bearer {os.environ.get('API_TOKEN', '')}",
            }
        )

    def process_task_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process image according to task data"""
        image_url = task_data["image_url"]
        task_id = task_data["task_id"]

        # Download image
        image_data = self._download_image(image_url)

        # Process image
        thumbnail_data = self._create_thumbnail(image_data)

        # Upload result
        upload_url = os.environ.get("IMAGE_UPLOAD_ENDPOINT")
        upload_response = self._upload_result(upload_url, thumbnail_data, task_id)

        return {
            "task_id": task_id,
            "original_size": len(image_data),
            "thumbnail_size": len(thumbnail_data),
            "api_response": upload_response,
        }

    def _download_image(self, url: str) -> bytes:
        """Download image from URL with retries"""
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(url, timeout=self.config.api_timeout)
                response.raise_for_status()
                return response.content
            except requests.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise
                time.sleep(self.config.retry_delay)

    def _create_thumbnail(self, image_data: bytes) -> bytes:
        """Create thumbnail from image data"""
        with Image.open(BytesIO(image_data)) as img:
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Create thumbnail
            img.thumbnail(self.config.thumbnail_size)

            # Save to bytes
            output = BytesIO()
            img.save(
                output,
                format=self.config.format,
                quality=self.config.quality,
                optimize=True,
            )
            return output.getvalue()

    def _upload_result(self, url: str, image_data: bytes, task_id: str) -> dict:
        """Upload processed image with retries"""
        files = {"image": (f"thumbnail_{task_id}.jpg", image_data, "image/jpeg")}
        data = {"task_id": task_id, "timestamp": datetime.utcnow().isoformat()}

        for attempt in range(self.config.max_retries):
            try:
                response = self.session.post(
                    url, files=files, data=data, timeout=self.config.api_timeout
                )
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise
                time.sleep(self.config.retry_delay)


if __name__ == "__main__":
    # Get configuration from environment
    config = ImageProcessingConfig(
        thumbnail_size=(
            int(os.environ.get("THUMBNAIL_WIDTH", 200)),
            int(os.environ.get("THUMBNAIL_HEIGHT", 200)),
        ),
        quality=int(os.environ.get("IMAGE_QUALITY", 85)),
        format=os.environ.get("IMAGE_FORMAT", "JPEG"),
        api_timeout=int(os.environ.get("API_TIMEOUT", 30)),
        max_retries=int(os.environ.get("MAX_RETRIES", 3)),
        retry_delay=int(os.environ.get("RETRY_DELAY", 5)),
    )

    # Create processor and consumer
    processor = ImageProcessor(config)
    consumer = TaskConsumer(
        queue_name=os.environ.get("QUEUE_NAME", "image_processing"),
        processor=processor,
        rabbit_host=os.environ.get("RABBIT_HOST", "localhost"),
    )

    consumer.start()
