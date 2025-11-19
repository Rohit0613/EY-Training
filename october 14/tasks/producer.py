import pika
import random
import time

# Connect to RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare a queue (it will create it if it doesn't exist)
channel.queue_declare(queue='task_queue', durable=True)

# Produce 10 messages
for i in range(10):
    item = random.randint(1, 100)
    message = str(item)
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        )
    )
    print(f" [x] Sent {message}")
    time.sleep(1)

print(" [x] Producer done.")
connection.close()
