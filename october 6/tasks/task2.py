import yaml
import logging

logging.basicConfig(level=logging.INFO,filename="task2_app.log",format='%(asctime)s %(levelname)s %(message)s')

config={
    "app":
        {"name": "Student Portal",
    "version": 1.0},
    "database":
        {"host": "localhost",
          "port": 3306,
           "user": "root"}
}

with open("task2_config.yaml","w") as f:
    yaml.dump(config,f)
    logging.info("Config written,yaml file created")
try:
   with open("task2_config.yaml", "r") as f:
        yaml.safe_load(f)
   logging.info("Config file opened")
   a=config.get("database",{})
   host=a.get("host")
   port=a.get("port")
   user=a.get("user")
   print(f"Connecting to {host}:{port} as {user}")
except FileNotFoundError as e:
    print(e)
    logging.error("Config file not found")
