import requests
import hashlib
import os

URL = "https://www.aasantarem.pt/wp-content/uploads/2025/11/Trail-Versao-Sprint-2026-Geral-Masc..pdf"

HASH_FILE = "pdf_hash.txt"

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")  # pulled from GitHub Secrets


def send_discord_alert(message: str):
    if not WEBHOOK_URL:
        print("No webhook configured.")
        return
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)


def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def get_current_hash() -> str:
    response = requests.get(URL)
    response.raise_for_status()
    return file_hash(response.content)


def main():
    # Load previous hash file (if exists)
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            previous_hash = f.read().strip()
    else:
        previous_hash = None

    current_hash = get_current_hash()

    if previous_hash is None:
        send_discord_alert("🔍 GitHub Actions: Started monitoring the PDF.")
        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
        return

    if current_hash != previous_hash:
        send_discord_alert(f"⚠️ **PDF changed!**\n{URL}")
        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
    else:
        print("No change detected.")


if __name__ == "__main__":
    main()

