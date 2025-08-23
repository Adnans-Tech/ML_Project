# import python's built-in logging module
import logging
# Import os utility module for file path operations
import os
# Import datetime module to timestamp log files with today's date
from datetime import datetime

# Name of the folder where log files will be stored
LOG_DIR="logs"
# Create the log directory if it doesn't exist
os.makedirs(LOG_DIR, exist_ok=True)

# Build a log file path like: logs/log.2023-03-15.log (changes.daily)   
LOG_FILE=os.path.join(
    LOG_DIR,
    f"log_{datetime.now().strftime('%Y-%m-%d')}.log"
)

# Configure the ROOT logger once for the whole application
logging.basicConfig(
# Write all logs to this file
    filename=LOG_FILE,
# log message format
#  %(asctime)s: timestamp
# %(levelname)s : log level (INFO, ERROR, etc.)
# %(message)s : the log message text
format='%(asctime)s %(levelname)s - %(message)s',
# Minimum level to log (INFO and above)
level =logging.INFO
)

def get_logger(name):
    """
    Returns a named logger that inherits the root logger's configuration above
    use different names per module (e.g., __name__) to identify sources
    """
    # Get (or create) a logger with the specified name
    logger=logging.getLogger(name)
    # Ensure this logger emits info and above (Can be customized per logger)
    logger.setLevel(logging.INFO)
    # Return the configured named logger
    return logger

