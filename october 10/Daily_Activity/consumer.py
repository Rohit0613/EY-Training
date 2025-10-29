import pika
import json
import time

from anyio import sleep

connection =pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue="Student_tasks")

def callback(ch, method, properties, body):
    task = json.loads(body)
    print("Received",task)

    time.sleep(5)
    print("task processed for student",task["student_id"])

channel.basic_consume(queue="Student_tasks", on_message_callback=callback, auto_ack=True)
print("waiting for message,press Ctrl+C to exit")
channel.start_consuming()