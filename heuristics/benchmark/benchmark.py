import os
import csv
import sys
import time

CURDIRNAME = os.path.dirname(__file__)
PAGESDIR_PATH = os.path.join(CURDIRNAME, "pages")
URLFILE_PATH = os.path.join(CURDIRNAME, "urls.txt")
OUTCSV_PATH = os.path.join(CURDIRNAME, "scores.csv")

sys.path.append(os.path.join(CURDIRNAME, "..", ".."))
from heuristics.dvsvc_scorers import get_link_scorer, get_page_scorer

PAGE_SCORER = get_page_scorer()
LINK_SCORER = get_link_scorer()


def run_pages():
    results = []

    for filename in os.listdir(PAGESDIR_PATH):
        filepath = os.path.join(PAGESDIR_PATH, filename)

        with open(filepath, "r") as file:
            page_html = file.read()

            t = time.time()
            score = PAGE_SCORER.get_score(page_html)

            print("[%2dms] %s, %s" % (1000 * (time.time() - t), filename, score.value))

            results.append((filename, score.value, score.matched_predicates))

    with open(OUTCSV_PATH, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Filename", "Page score", "Keywords"])
        writer.writerows(results)

    print("Mean pscore:", sum([score for _, score, _ in results]) / len(results))
    print("Least pscore:", min([score for _, score, _ in results]))
    print("Greatest pscore:", max([score for _, score, _ in results]))
    print("Total pages:", len(results))
    pscore_under_09 = [
        (filename, score) for filename, score, _ in results if score < 0.9
    ]
    print("pscore < 0.9:", len(pscore_under_09), pscore_under_09)


def run_links():
    with open(URLFILE_PATH, "r") as file:
        urls = file.read().splitlines()
        urls = [url for url in urls if not url.startswith("#")]

    scores = {}

    for url in urls:
        scores[url] = LINK_SCORER.get_score(url, 0).value

    print("Mean lscore:", sum(scores.values()) / len(scores))
    print("Least lscore:", min(scores.values()))
    print("Greatest lscore:", max(scores.values()))
    print("Total links:", len(scores))
    lscore_under_09 = [(url, score) for url, score in scores.items() if score < 0.9]
    print("lscore < 0.9:", len(lscore_under_09), lscore_under_09)


if __name__ == "__main__":
    input("Run lscore? (Enter)")
    run_links()
    input("Run pscore? (Enter)")
    run_pages()
