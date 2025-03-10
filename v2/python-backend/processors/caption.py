import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List

import requests
from llm.joycaption import generate_caption, generate_tags
from task_processor import TaskConsumer, TaskProcessor, Config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class JoyCaptionConfig(Config):
    pass


class JoyCaptionProcessor(TaskProcessor):
    """Processor for extracting and analyzing EXIF data from images"""

    def __init__(self, config: JoyCaptionConfig):
        super().__init__()
        self.config = config

    def process_task_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process image EXIF data"""
        image_url = task_data["image_url"]
        task_id = task_data["task_id"]

        # Download image
        image_data = self._download_image(image_url)

        caption = None
        try:
            caption = generate_caption(image_data)
        except Exception as e:
            print(e)

        tags = []
        try:
            tags = generate_tags(image_data)
        except Exception as e:
            print(e)

        return {"task_id": task_id, "caption": caption, "tags": tags}


if __name__ == "__main__":
    # Configuration
    config = JoyCaptionConfig(
        api_timeout=int(os.environ.get("API_TIMEOUT", 30)),
        max_retries=int(os.environ.get("MAX_RETRIES", 3)),
        retry_delay=int(os.environ.get("RETRY_DELAY", 5)),
    )

    # Create processor and consumer
    processor = JoyCaptionProcessor(config)
    consumer = TaskConsumer(
        queue_name=os.environ.get("QUEUE_NAME", "exif_processing"),
        processor=processor,
        rabbit_host=os.environ.get("RABBIT_HOST", "localhost"),
    )

    consumer.start()
