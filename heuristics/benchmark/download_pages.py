import gzip
import re
import os

from urllib.request import Request, urlopen
from urllib.error import URLError


CURDIRNAME = os.path.dirname(__file__)
URLFILE_PATH = os.path.join(CURDIRNAME, "urls.txt")
OUTDIR_PATH = os.path.join(CURDIRNAME, "pages")

if not os.path.exists(OUTDIR_PATH):
    os.makedirs(OUTDIR_PATH)

with open(URLFILE_PATH, "r") as file:
    urls = file.read().splitlines()
    urls = [url for url in urls if not url.startswith("#")]

for url in urls:
    try:
        req = Request(
            url=url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp = urlopen(req)
        print("Downloaded", url)
    except URLError as e:
        print(f"Failed to download {url} - ", str(e))
        continue

    page_html = gzip.decompress(resp.read()) if resp.headers.get(
        "Content-Encoding") == "gzip" else resp.read()

    page_charset = resp.headers.get_content_charset()
    if page_charset:
        page_html = page_html.decode(page_charset)
    else:
        page_html = page_html.decode("utf-8")

    filename = url.replace("https:", "").replace(
        "http:", "").replace("www.", "")
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    filename += ".txt"

    with open(os.path.join(OUTDIR_PATH, filename), "w") as file:
        file.write(page_html)
