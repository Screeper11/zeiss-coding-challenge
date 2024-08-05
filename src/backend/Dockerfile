FROM python:3.12-slim

RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    useradd -m appuser

WORKDIR /app

# Copy poetry files and install dependencies
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application files
COPY src/backend/api.py .
COPY *.env .

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
