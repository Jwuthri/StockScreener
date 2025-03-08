#!/usr/bin/env python
"""
Script to schedule the daily stock update job.
This sets up a scheduler to run the daily_stock_update.py script once per day.
"""

import logging
import subprocess
import sys
import time
from pathlib import Path

import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(Path(__file__).parent / "scheduler.log"), logging.StreamHandler()],
)

logger = logging.getLogger("scheduler")

# Path to the daily stock update script
SCRIPT_PATH = str(Path(__file__).parent / "daily_stock_update.py")


def run_job():
    """Run the daily stock update job."""
    logger.info("Running daily stock update job")

    try:
        # Run the script as a subprocess
        result = subprocess.run([sys.executable, SCRIPT_PATH], capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("Daily stock update completed successfully")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"Daily stock update failed with exit code {result.returncode}")
            logger.error(f"Error: {result.stderr}")
    except Exception as e:
        logger.error(f"Error running daily stock update: {str(e)}")


def main():
    """Main function to set up the scheduler."""
    logger.info("Starting scheduler for daily stock update")

    # Define the time to run the job (16:30 = 4:30 PM, after market close)
    schedule_time = "16:30"

    # Schedule the job to run daily at the specified time
    schedule.every().day.at(schedule_time).do(run_job)

    logger.info(f"Job scheduled to run daily at {schedule_time}")

    # Run the job immediately for the first time
    logger.info("Running job immediately for the first time")
    run_job()

    # Keep the script running indefinitely
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    run_job()
