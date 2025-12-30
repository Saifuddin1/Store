from flask import flash, redirect
import traceback
import logging
import pytz
from datetime import datetime



class ISTFormatter(logging.Formatter):
    """Custom logging formatter to enforce IST timezone."""

    def formatTime(self, record, datefmt=None):
        ist = pytz.timezone("Asia/Kolkata")  # Set timezone to IST
        local_dt = datetime.fromtimestamp(record.created, ist)
        return local_dt.strftime(datefmt if datefmt else "%Y-%m-%d %H:%M:%S")


# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format=(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ),

    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ],
)

logger = logging.getLogger("app")

formatter = ISTFormatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

for handler in logger.handlers:
    handler.setFormatter(formatter)


priority_order = {'High': 1, 'Moderate': 2, 'Low': 3}
wip = "work in progress"
done = "done"


def handle_exception(e, redirect_url, message="Something went wrong"):
    logger.error(traceback.format_exc())
    logger.info(f"Exception occurred: {e}")
    flash(message, 'danger')
    return redirect(redirect_url)
