import json
import logging
import os
import queue as queue_lib
import signal
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import pika
import requests

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
class Config:
    api_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5


@dataclass
class ProcessingResult:
    status: ProcessingStatus
    message: str
    retry_count: int
    processing_time: float
    error: Optional[Exception] = None


class TaskProcessor:
    """Base class for task processing"""

    def __init__(self):
        self.max_retries = 3
        self.processing_stats = {"processed": 0, "failed": 0, "retried": 0}
        self._stats_lock = threading.Lock()

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "TaskProcessor/1.0",
                "Authorization": f"Bearer {os.environ.get('API_TOKEN', '')}",
            }
        )

        self.config = Config(
            api_timeout=int(os.environ.get("API_TIMEOUT", 30)),
            max_retries=int(os.environ.get("MAX_RETRIES", 3)),
            retry_delay=int(os.environ.get("RETRY_DELAY", 5)),
        )

    def update_stats(self, result: ProcessingResult):
        """Thread-safe update of processing statistics"""
        with self._stats_lock:
            self.processing_stats["processed"] += 1
            if result.status == ProcessingStatus.FAILED:
                self.processing_stats["failed"] += 1
            elif result.status == ProcessingStatus.RETRY:
                self.processing_stats["retried"] += 1

    def process_task(
        self, task_data: Dict[str, Any], retry_count: int = 0
    ) -> ProcessingResult:
        """Process a single task"""
        start_time = time.time()
        task_id = task_data.get("task_id")

        try:
            logger.info(f"Processing task {task_id} (attempt {retry_count + 1})")

            self._validate_task(task_data)
            result_data = self.process_task_data(task_data)
            self._update_task_status(task_id, result_data)

            processing_time = time.time() - start_time
            result = ProcessingResult(
                status=ProcessingStatus.SUCCESS,
                message=f"Successfully processed task {task_id}",
                retry_count=retry_count,
                processing_time=processing_time,
                result_data=result_data,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            if retry_count < self.max_retries:
                status = ProcessingStatus.RETRY
                message = f"Task {task_id} failed, will retry. Error: {str(e)}"
            else:
                status = ProcessingStatus.FAILED
                message = f"Task {task_id} failed permanently. Error: {str(e)}"

            result = ProcessingResult(
                status=status,
                message=message,
                retry_count=retry_count,
                processing_time=processing_time,
                error=e,
            )

            logger.error(result.message)

        self.update_stats(result)
        return result

    def _validate_task(self, task_data: Dict[str, Any]):
        required_fields = ["task_id", "image_url"]
        missing_fields = [field for field in required_fields if field not in task_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        if not task_data["image_url"].startswith(("http://", "https://")):
            raise ValueError("Invalid image URL")

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
                logger.error(f"Download attempt {attempt + 1} failed: {e}")
                time.sleep(self.config.retry_delay)

    def process_task_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the task data"""
        raise NotImplementedError("Subclasses must implement _process_task_data")

    def _update_task_status(self, task_id: str, result_data: Dict[str, Any]):
        """Update task status in external system"""
        status_url = os.environ.get("API_STATUS_ENDPOINT")
        if status_url:
            try:
                response = self.session.post(
                    status_url,
                    json={
                        "task_id": task_id,
                        "status": "completed",
                        "exif_data": result_data,
                    },
                    timeout=self.config.api_timeout,
                )
                response.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Failed to update task status: {e}")
                raise


class TaskConsumer:
    """Consumes tasks from RabbitMQ and manages processing"""

    def __init__(
        self, queue_name: str, rabbit_host: str = "localhost", prefetch_count: int = 1
    ):
        self.queue_name = queue_name
        self.rabbit_host = rabbit_host
        self.prefetch_count = prefetch_count
        self.processor = TaskProcessor()
        self.should_stop = False
        self.work_queue = queue_lib.Queue(maxsize=100)
        self.worker_threads = []

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def connect(self):
        """Establish connection to RabbitMQ"""
        while not self.should_stop:
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.rabbit_host)
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                self.channel.basic_qos(prefetch_count=self.prefetch_count)
                logger.info(f"Connected to RabbitMQ, consuming from {self.queue_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                time.sleep(5)
        return False

    def start(self, num_threads: int = 4):
        """Start the consumer with multiple worker threads"""
        if not self.connect():
            return

        # Start worker threads
        for _ in range(num_threads):
            thread = threading.Thread(target=self._worker_thread)
            thread.daemon = True
            thread.start()
            self.worker_threads.append(thread)

        # Start consuming
        self.channel.basic_consume(
            queue=self.queue_name, on_message_callback=self._handle_message
        )

        try:
            logger.info("Starting to consume messages...")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Error while consuming: {e}")
        finally:
            self.shutdown()

    def _worker_thread(self):
        """Worker thread that processes tasks from the work queue"""
        while not self.should_stop:
            try:
                work_item = self.work_queue.get(timeout=1)
                if work_item is None:
                    break

                delivery_tag, body = work_item
                message = json.loads(body)

                result = self.processor.process_task(
                    message, retry_count=message.get("retry_count", 0)
                )

                if result.status == ProcessingStatus.SUCCESS:
                    self.channel.basic_ack(delivery_tag)
                elif result.status == ProcessingStatus.RETRY:
                    # Requeue with incremented retry count
                    message["retry_count"] = result.retry_count + 1
                    self.channel.basic_publish(
                        exchange="",
                        routing_key=self.queue_name,
                        body=json.dumps(message),
                    )
                    self.channel.basic_ack(delivery_tag)
                else:  # FAILED
                    # Could move to dead letter queue here
                    self.channel.basic_nack(delivery_tag, requeue=False)

            except queue_lib.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in worker thread: {e}")

    def _handle_message(self, ch, method, properties, body):
        """Callback for received messages"""
        try:
            self.work_queue.put((method.delivery_tag, body))
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received, stopping consumer...")
        self.should_stop = True
        if hasattr(self, "channel") and self.channel:
            self.channel.stop_consuming()

    def shutdown(self):
        """Graceful shutdown"""
        self.should_stop = True

        # Stop accepting new messages
        if hasattr(self, "channel") and self.channel:
            self.channel.stop_consuming()

        # Wait for worker threads to finish
        for _ in self.worker_threads:
            self.work_queue.put(None)

        for thread in self.worker_threads:
            thread.join(timeout=5)

        # Close connection
        if hasattr(self, "connection") and self.connection:
            self.connection.close()

        logger.info("Consumer shutdown complete")
        logger.info(f"Final stats: {self.processor.processing_stats}")
