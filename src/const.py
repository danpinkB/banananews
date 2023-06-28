import os
import pathlib
from dotenv import load_dotenv

load_dotenv()

INDEX_DB_FILE = pathlib.Path(os.getcwd()) / "articles.db"
SELENIUM_REMOTE_DRIVER = os.environ.get("SELENIUM_REMOTE_DRIVER")
DATA_FOLDER = pathlib.Path(os.getcwd()) / "data"

