import logging
import os

# Make sure the logs directory exists
LOG_DIR = os.environ.get("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Set up logger
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'server.log'),
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_request(ip, method, path):
    logging.info(f"{ip} - {method} {path}")