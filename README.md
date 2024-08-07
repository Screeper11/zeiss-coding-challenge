# ZEISS Coding Challenge

## Overview

This project is a full-stack application that interacts with the arXiv API to search for and store academic papers. It
consists of a backend API built with FastAPI, a PostgreSQL database, and a frontend built with React.

## Features

- Search arXiv for papers by author, title, or journal
- Store search queries and results in a PostgreSQL database
- Retrieve past queries within a specified time range
- Display search results with pagination

## Tech Stack

- Backend: FastAPI, SQLAlchemy, PostgreSQL
- Frontend: React, HTMX
- DevOps: Docker, docker-compose

## Setup and Installation

1. Prerequisites:
    - Python 3.9+
    - Docker and Docker Compose
    - Poetry

2. Build and run the Docker containers:
   ```shell
   docker-compose up --build
   ```

3. Access the application:
    - http://localhost:5001

## API Endpoints

- `POST /arxiv`: Search arXiv and store results
- `GET /queries`: Retrieve past queries
- `GET /results`: Get stored search results

For detailed API documentation, visit http://localhost:8000/docs after starting the application.

## Running Tests

To run the backend tests:

```shell
docker-compose run api pytest
```

To run the frontend tests:

```shell
docker-compose run frontend pytest
```
