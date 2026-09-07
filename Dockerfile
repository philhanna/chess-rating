# syntax=docker/dockerfile:1

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/rating

RUN groupadd --system rating \
    && useradd --system --gid rating --create-home --home-dir /home/rating rating \
    && mkdir -p /home/rating/.config/chess-rating \
    && chown -R rating:rating /home/rating

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY rating ./rating

RUN python -m pip install --no-cache-dir .

USER rating

ENTRYPOINT ["rating"]
CMD ["--help"]
