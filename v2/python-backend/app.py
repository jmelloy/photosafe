import pika
import json
import time
from typing import List, Dict
import logging
from dataclasses import dataclass
import threading
from flask import Flask, request, jsonify
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class QueueConfig:
    name: str
    routing_key: str
    handler_function: str


class TaskOrchestrator:
    def __init__(self, rabbit_host: str = "localhost"):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbit_host)
        )
        self.channel = self.connection.channel()
        self.exchange_name = "task_exchange"

        # Declare exchange
        self.channel.exchange_declare(
            exchange=self.exchange_name, exchange_type="direct", durable=True
        )

        # Define queue configurations
        self.queues = [
            QueueConfig("validation_queue", "validation", "validate_id"),
            QueueConfig("processing_queue", "processing", "process_id"),
            QueueConfig("notification_queue", "notification", "send_notification"),
            QueueConfig("analytics_queue", "analytics", "log_analytics"),
        ]

        # Declare all queues
        for queue in self.queues:
            self.channel.queue_declare(queue=queue.name, durable=True)
            self.channel.queue_bind(
                exchange=self.exchange_name,
                queue=queue.name,
                routing_key=queue.routing_key,
            )

    def publish_task(self, task_id: str, data: dict) -> Dict:
        """Publish task_id to all queues and return task details"""
        publish_time = time.time()
        queues_published = []

        for queue in self.queues:
            message = json.dumps(
                {
                    "task_id": task_id,
                    "timestamp": publish_time,
                    "handler": queue.handler_function,
                    "data": data,
                }
            )

            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=queue.routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2, content_type="application/json"
                ),
            )
            queues_published.append(queue.name)
            logger.info(f"Published task_id {task_id} to queue {queue.name}")

        return {
            "task_id": task_id,
            "timestamp": publish_time,
            "queues": queues_published,
            "status": "published",
        }

    def close(self):
        self.connection.close()


# Flask application
app = Flask(__name__)
orchestrator = None


@app.before_first_request
def initialize_orchestrator():
    global orchestrator
    rabbit_host = os.environ.get("RABBIT_HOST", "localhost")
    orchestrator = TaskOrchestrator(rabbit_host)


@app.route("/tasks", methods=["POST"])
def create_task():
    """
    Create a new task and distribute it to all queues

    Expected POST body:
    {
        "task_id": "optional-custom-id"  # If not provided, a UUID will be generated
    }
    """
    try:
        data = request.get_json() or {}
        task_id = data.get("task_id", str(uuid.uuid4()))

        if not isinstance(task_id, str):
            return jsonify({"error": "task_id must be a string"}), 400

        result = orchestrator.publish_task(task_id, data)
        return jsonify(result), 202

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": time.time()})


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
