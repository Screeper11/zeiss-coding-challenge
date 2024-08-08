# ZEISS Coding Challenge

## Overview

This project is a full-stack application that interacts with the arXiv API to search for and store academic papers. It
consists of a backend API built with FastAPI, a PostgreSQL database, and a frontend built with FastHTML.

## Features

- Search arXiv for papers by author, title, or journal
- Store search queries and results in a PostgreSQL database
- Retrieve past queries within a specified time range
- Display search results with pagination

## Tech Stack

- **Backend:** FastAPI
- **Database:** PostgreSQL
- **Frontend:** FastHTML
- **DevOps:** Docker
- **Deployment:** Azure

## Deployment

The application is hosted and accessible at [zeiss.screeper.dev](https://zeiss.screeper.dev).

## Setup and Installation

1. **Prerequisites:**
    - Python 3.12+
    - Poetry
    - Docker and Docker Compose


2. **Build and run the Docker containers:**
   ```shell
   docker-compose up --build
   ```

3. **Access the application:**
    - Frontend: http://localhost:5001
    - Backend API: http://localhost:8000
    - API Documentation: http://localhost:8000/docs

## API Endpoints

- `POST /arxiv`: Search arXiv and store results
- `GET /queries`: Retrieve past queries
- `GET /results`: Get stored search results

For detailed API documentation, visit [zeiss.screeper.dev/docs](https://zeiss.screeper.dev/docs).

## Running Tests

Ensure that the Docker containers are running before executing the tests.

**Run backend tests:**

```shell
pytest backend/tests
```

**Run frontend tests:**

```shell
pytest frontend/tests
```

## Development

To set up the development environment:

1. Install dependencies:
   ```shell
   poetry install
   ```

2. Activate the virtual environment:
   ```shell
   poetry shell
   ```

3. Run the application in development mode:
   ```shell
   uvicorn backend.src.main:app --reload
   python frontend/src/main.py
   ```
