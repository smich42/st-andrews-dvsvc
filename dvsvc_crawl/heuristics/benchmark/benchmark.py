import os
import csv
from dvsvc_crawl.heuristics.dvsvc_scorers import *
from dvsvc_crawl.heuristics.scorers import *

CURDIRNAME = os.path.dirname(__file__)
PAGESDIR_PATH = os.path.join(CURDIRNAME, "pages")
OUTCSV_PATH = os.path.join(CURDIRNAME, "scores.csv")

PAGE_SCORER = get_page_scorer()


def run():
    results = []

    for filename in os.listdir(PAGESDIR_PATH):
        filepath = os.path.join(PAGESDIR_PATH, filename)

        with open(filepath, "r") as file:
            page_html = file.read()
            score = PAGE_SCORER.get_score(page_html)
            results.append((filename, score.value, score.matched_predicates))

    with open(OUTCSV_PATH, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Filename", "Page score", "Keywords"])
        writer.writerows(results)

    print("Mean score:", sum(
        [score for _, score, _ in results]) / len(results))
    print("Least score:", min([score for _, score, _ in results]))
    print("Greatest score:", max([score for _, score, _ in results]))
    print("Scores under 0.9:", len(
        [score for _, score, _ in results if score < 0.9]))
    print("Total pages:", len(results))
    print("Pages under 0.9:", [
        (filename, score) for filename, score, _ in results if score < 0.9])


if __name__ == "__main__":
    run()
