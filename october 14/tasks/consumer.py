import pika
import time

# Connect to RabbitMQ server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare the same queue (must match the producer)
channel.queue_declare(queue='task_queue', durable=True)

def callback(ch, method, properties, body):
    item = body.decode()
    print(f" [x] Received {item}")
    time.sleep(2)  # Simulate processing time
    print(f" [✓] Done processing {item}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

# Consume messages from the queue
channel.basic_qos(prefetch_count=1)  # Fair dispatch
channel.basic_consume(queue='task_queue', on_message_callback=callback)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()

