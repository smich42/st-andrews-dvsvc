# st-andrews-dvsvc
A web crawler to identify domestic violence support services in Scotland.

## Running the crawler
Crawls with plain CSV output are currently supported: specify `./simple-run.sh <output-file>`. For particular features like job [persistence](https://docs.scrapy.org/en/latest/topics/jobs.html), run using `scrapy crawl dvsvc <args...>`.
