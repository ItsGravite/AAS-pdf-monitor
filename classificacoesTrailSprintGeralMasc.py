import requests
import hashlib
import os
from bs4 import BeautifulSoup

PAGE_URL = "https://www.aasantarem.pt/classificacoes-campeonato-circuito-de-trail-versao-sprint-2026/"
HASH_FILE = "pdf_hash.txt"
TARGET_TEXT = "Trail Versão Sprint 2026 Geral Masc."
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")


def send_discord_alert(message: str):
    if not WEBHOOK_URL:
        print("No webhook configured.")
        return
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)


def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def get_pdf_url() -> str:
    """Scrapes the page to find the PDF with the exact link text."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(PAGE_URL, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for link in soup.find_all("a"):
        text = link.get_text(strip=True)
        href = link.get("href")
        if TARGET_TEXT.lower() in text.lower() and href and href.endswith(".pdf"):
            return href

    raise RuntimeError(f"Could not find PDF with text: {TARGET_TEXT}")


def get_current_hash(pdf_url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(pdf_url, headers=headers)
    response.raise_for_status()
    return file_hash(response.content)


def main():
    try:
        pdf_url = get_pdf_url()
    except Exception as e:
        send_discord_alert(f"❌ Error finding PDF: {e}")
        return

    # Load previous hash
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            previous_hash = f.read().strip()
    else:
        previous_hash = None

    # Fetch new hash
    try:
        current_hash = get_current_hash(pdf_url)
    except Exception as e:
        send_discord_alert(f"❌ Error downloading PDF: {e}")
        return

    # First run
    if previous_hash is None:
        send_discord_alert(f"🔍 Started monitoring:\n{pdf_url}")
        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
        return

    # Compare
    if current_hash != previous_hash:
        send_discord_alert(f"⚠️ **PDF changed!**\n{pdf_url}")
        with open(HASH_FILE, "w") as f:
            f.write(current_hash)
    else:
        print("No change detected.")


if __name__ == "__main__":
    main()
