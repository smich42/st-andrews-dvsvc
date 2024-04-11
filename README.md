# st-andrews-dvsvc

A web crawler to identify domestic violence support services in Scotland.

## Use with Docker

Run `docker-compose up` to start three containers:

* `app` (the crawler)
* `db` (the PostgreSQL database server)
* `pgadmin`

This will automatically load `.env` from the project directory. Set one up as per `example.env`.

Access pgAdmin at `localhost:5051/` from a browser (as specified in `compose.yaml`).

## Run just the crawler (without Docker)

Crawls with plain CSV output are currently supported: specify `./simple-run.sh <output-file>`. For particular features like job [persistence](https://docs.scrapy.org/en/latest/topics/jobs.html), run using `scrapy crawl dvsvc <args...>`.
