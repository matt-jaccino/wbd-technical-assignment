# exercise 2

FROM python:3.12-slim-bookworm

RUN set -ex \
    && apt-get update \
    && apt-get upgrade -y \
    && adduser --system --no-create-home myuser \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR C:/Users/mattj/Downloads/wbd-assignment

COPY ./my-web-server.py my-web-server.py

EXPOSE 8000

CMD ["python", "my-web-server.py"]

USER myuser
