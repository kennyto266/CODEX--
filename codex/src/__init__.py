"""
RSI Backtest Optimizer
A quantitative trading system for optimizing RSI parameters on Hong Kong stocks.
"""

import logging
from datetime import datetime
import os

__version__ = "1.0.0"

def setup_logging(log_level="INFO", log_dir="results/logs"):
    """
    Configure logging for the RSI backtest optimizer.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files

    Returns:
        Logger instance
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Generate timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"backtest_{timestamp}.log")

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger("rsi_backtest")
    logger.info(f"RSI Backtest Optimizer v{__version__}")
    logger.info(f"Log file: {log_filename}")

    return logger
