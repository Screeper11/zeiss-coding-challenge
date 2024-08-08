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

- **Backend:** FastAPI
- **Database:** PostgreSQL
- **Frontend:** FastHTML
- **DevOps:** Docker
- **Deployment:** Azure

## Setup and Installation

1. **Prerequisites:**
    - Python 3.9+
    - Poetry
    - Docker and Docker Compose

2. **Build and run the Docker containers:**
   ```shell
   docker-compose up --build
   ```

3. **Access the application:**
    - http://localhost:5001

## API Endpoints

- `POST /arxiv`: Search arXiv and store results
- `GET /queries`: Retrieve past queries
- `GET /results`: Get stored search results

For detailed API documentation, visit http://localhost:8000/docs after starting the application.

## Running Tests

**Run backend tests:**

```shell
pytest backend/tests
```

_To run the backend tests make sure the Docker containers are running!_

**Run frontend tests:**

```shell
pytest frontend/tests
```
