from dotenv import load_dotenv
from pathlib import Path
import sys
import os



CURRENT_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = CURRENT_DIR.parent

P1_ROOT = PROJECT_ROOT / "project01(storagevc)"

if str(P1_ROOT) not in sys.path:
    sys.path.insert(0, str(P1_ROOT))

ENV_PATH = P1_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL_NAME = "llama-3.3-70b-versatile"