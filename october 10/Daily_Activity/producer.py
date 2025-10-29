import pika
import json

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue="Student_task")

task = {
    "Student_id": 101,
    "Action": "generate_certificate",
    "email": "aniket@gmail.com"
}

channel.basic_publish(
    exchange='',
    routing_key='Student_task',
    body=json.dumps(task)
)

print("tasks sent to queue:", task)

connection.close()