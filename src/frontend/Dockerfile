FROM python:3.12-slim

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    useradd -m appuser

WORKDIR /app

# Copy poetry files and install dependencies
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application files
COPY src/frontend/frontend.py .
COPY src/frontend/assets ./assets
COPY src/frontend/assets/favicon.ico .
COPY *.env .

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5001

CMD ["python", "frontend.py"]
