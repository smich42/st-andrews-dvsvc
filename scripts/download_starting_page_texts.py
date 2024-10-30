import os
import requests
from bs4 import BeautifulSoup
import hashlib
from pathlib import Path
from json import dumps as json_dumps


IN_FILE = "../resource/starting_links.txt"
OUT_DIR = "../resource/starting_page_texts"


def url_to_filename(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest() + ".json"


def download_and_parse(url: str, outpath: str) -> bool:
    url = url.strip()

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url.strip(), headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator="\n")
        cleaned_text = "\n".join(
            line.strip() for line in text.splitlines() if line.strip()
        )

        filepath = os.path.join(outpath, url_to_filename(url))

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_dumps({"url": url, "text": cleaned_text}))

        print(f"Wrote {url} -> {filepath}")

    except Exception as e:
        print(f"Error for {url}: {e}")
        return False

    return True


def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    try:
        with open(IN_FILE, "r") as f:
            urls = f.readlines()
    except FileNotFoundError:
        print(f"Error: {IN_FILE} not found")
        return

    for url in urls:
        download_and_parse(url, OUT_DIR)


if __name__ == "__main__":
    main()
