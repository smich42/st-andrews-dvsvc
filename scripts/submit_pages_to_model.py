import os
import requests
import json
import hashlib
import logging
from datetime import datetime
from tld import get_fld
from typing import Dict, List, Any
from datetime import datetime

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

PAGE_TEXTS_DIR = "../resource/starting_page_texts"
OUT_DIR = "../resource/llm_responses"
MODEL_URL = "http://localhost:11434/api/generate"
PROMPT_START = ""
CONTEXT_TOKENS = 4096


def url_to_filename(url: str, timestamp: datetime) -> str:
    return (
        hashlib.md5(url.encode()).hexdigest()
        + "_"
        + timestamp.strftime("%Y%m%d_%H%M%S")
        + ".json"
    )


def read_json(path: str) -> Dict[str, str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading {path}: {e}")


def group_pages_by_fld(
    page_data_list: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    groups = {}

    # Each webpage is its own file
    for page_data in page_data_list:
        url = page_data["url"]

        try:
            # Get FLD
            domain = get_fld(url, fail_silently=True)
            if not domain:
                logging.warning("Could not get FLD: " + url)
                continue

            # Get prompt part for this webpage
            prompt_part = {
                "url": url,
                "headings": [],  # TODO: populate this field
                "paragraph_text": page_data.get("text", ""),
            }

            if domain not in groups:
                groups[domain] = []
            groups[domain].append(prompt_part)

        except Exception as e:
            logging.error(f"Error processing URL {url}: {e}")
            continue

    return groups


def submit_to_llm(prompt: str) -> Dict[str, Any]:
    try:
        response = requests.post(
            MODEL_URL,
            json={
                "model": "dvsvc-llm",
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": CONTEXT_TOKENS},
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error submitting prompt to Ollama API: {e}")
        return None


def write_response(domain: str, prompt: str, response: Dict[str, Any]) -> None:
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    filepath = os.path.join(OUT_DIR, url_to_filename(domain, datetime.now()))
    output_data = {
        "prompt": prompt,
        "response": response,
    }

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json.dumps(output_data))
        logging.info(f"Saved response to {filepath}")
    except Exception as e:
        logging.error(f"Error saving response to {filepath}: {e}")


def main():
    page_data_list = []
    for filename in os.listdir(PAGE_TEXTS_DIR):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(PAGE_TEXTS_DIR, filename)
        contents = read_json(filepath)
        if contents:
            page_data_list.append(contents)

    grouped = group_pages_by_fld(page_data_list)
    n_grouped = len(grouped)

    for i, (domain, pages) in enumerate(grouped.items()):
        logging.info(
            f"[{i + 1}/{n_grouped}] Processing {domain} with {len(pages)} page(s)"
        )

        prompt = PROMPT_START + json.dumps(pages)
        response = submit_to_llm(prompt)

        write_response(domain, prompt, response)


if __name__ == "__main__":
    main()
