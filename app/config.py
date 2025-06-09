from dotenv import load_dotenv
import os

load_dotenv()

PASSPHRASE = os.getenv("PASSPHRASE", "default_passphrase")