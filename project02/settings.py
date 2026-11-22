from dotenv import load_dotenv
from pathlib import Path
import sys
import os



CURRENT_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = CURRENT_DIR.parent

P1_ROOT = PROJECT_ROOT / "project01(storagevc)"

if str(P1_ROOT) not in sys.path:
    sys.path.insert(0, str(P1_ROOT))

ROOT_ENV = PROJECT_ROOT / ".env"
P1_ENV = P1_ROOT / ".env"

# Root .env is the documented setup file. An existing project01 .env
# still wins so a local override keeps working.
if ROOT_ENV.exists():
    load_dotenv(dotenv_path=ROOT_ENV)
if P1_ENV.exists():
    load_dotenv(dotenv_path=P1_ENV, override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL_NAME = os.getenv("GENERATION_MODEL")