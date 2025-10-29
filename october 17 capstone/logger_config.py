import logging
from logging.handlers import RotatingFileHandler

# Centralized logger
logger = logging.getLogger("patient_health")
logger.setLevel(logging.INFO)

handler = RotatingFileHandler("patient_health.log", maxBytes=5*1024*1024, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
