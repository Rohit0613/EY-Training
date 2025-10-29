import threading
import queue
import random
import time

task_queue = queue.Queue()

def data_generator():
    for _ in range(10):
        value = random.randint(10, 99)
        task_queue.put(value)
        print(f"[Generator] Created task: {value}")
        time.sleep(1)

    task_queue.put(None)
    print("[Generator] All tasks created.")

def data_worker():
    while True:
        task = task_queue.get()
        if task is None:
            break
        print(f"[Worker] Processing task: {task}")
        time.sleep(2)

    task_queue.put(None)
    print("[Worker] Finished all tasks.")

generator_thread = threading.Thread(target=data_generator)
worker_thread = threading.Thread(target=data_worker)

generator_thread.start()
worker_thread.start()

generator_thread.join()
worker_thread.join()

print("[Main] Task processing completed.")
