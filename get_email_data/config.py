import os

# ============================================================
# Gmail Configuration
# ============================================================

GMAIL_USER = "mobashshir.taj@gmail.com"

PASSWORD_FILE = "app_pass_gmai_emaiBot.txt"

with open(PASSWORD_FILE, "r", encoding="utf-8") as file:
    APP_PASSWORD = file.read().strip()


# ============================================================
# Gmail / IMAP Settings
# ============================================================

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

# Number of emails fetched in one batch.
#
# 50 is safer for Gmail and large emails.
# You can increase to 100 later if everything is stable.
BATCH_SIZE = 50

# Socket timeout in seconds.
IMAP_TIMEOUT = 60


# ============================================================
# Directories
# ============================================================

OUTPUT_DIRECTORY = "output"
IMAGE_DIRECTORY = "downloaded_images"

os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
os.makedirs(IMAGE_DIRECTORY, exist_ok=True)