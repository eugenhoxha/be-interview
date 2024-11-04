"""
This module configures logging for the application.
"""
import logging
from datetime import datetime

log_filename = f"logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode='w'),
        logging.StreamHandler()
    ],
)

logger = logging.getLogger(__name__)