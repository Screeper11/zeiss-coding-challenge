FROM python:3.12-slim

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    useradd -m appuser

WORKDIR /app

# Copy poetry files and install dependencies
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application files
COPY frontend/src ./src
COPY frontend/src/assets ./assets
COPY frontend/src/assets/favicon.ico .
COPY *.env ./src

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

CMD python /app/src/main.py
