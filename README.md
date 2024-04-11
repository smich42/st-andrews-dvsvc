# st-andrews-dvsvc

A web crawler to identify domestic violence support services in Scotland.

## Use with Docker

After building the image with `docker compose build`, run `docker compose up` to start three containers:

* `app` (the crawler)
* `db` (the PostgreSQL database server)
* `pgadmin`

This automatically loads environment variables from `.env` in the project directory. Set one up as per `example.env`.

`docker compose run db pgadmin` will only spin up the database and pgAdmin containers. Access pgAdmin at `localhost:5051/` from a browser (as specified in `compose.yaml`).

## Run just the crawler (without Docker)

Specify `./simple-run.sh <output-file>` for a crawl with plain CSV output. For particular features like job [persistence](https://docs.scrapy.org/en/latest/topics/jobs.html), run using `scrapy crawl dvsvc <args...>`.
