import logging
import os

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/mis.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("RetailMIS")

def log(message, level="info"):
    getattr(logger, level)(message)