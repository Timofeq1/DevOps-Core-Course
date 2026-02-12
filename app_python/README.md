# DevOps Info Service

[![Python CI](https://github.com/timofeq1/DevOps-Core-Course/actions/workflows/python-ci.yml/badge.svg)](https://github.com/timofeq1/DevOps-Core-Course/actions/workflows/python-ci.yml)
[![codecov](https://codecov.io/gh/timofeq1/DevOps-Core-Course/graph/badge.svg?token=CODECOV_TOKEN)](https://codecov.io/gh/timofeq1/DevOps-Core-Course)

## Overview
A production-ready Python web service that provides comprehensive system information and health monitoring. Built with FastAPI.

## Prerequisites
- Python 3.10+
- pip (Python package installer)

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Standard run:
```bash
python app.py
```
The application will start on `http://0.0.0.0:5000` by default.

Custom configuration:
```bash
HOST=127.0.0.1 PORT=8080 python app.py
```

## API Endpoints

### GET /
Returns service metadata and system information.

Response:
```json
{
  "service": { ... },
  "system": { ... },
  "runtime": { ... },
  "request": { ... },
  "endpoints": [ ... ]
}
```

### GET /health
Returns health status and uptime.

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28...",
  "uptime_seconds": 120
}
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| HOST | Bind host address | 0.0.0.0 |
| PORT | Listen port | 5000 |

## Docker

### Build Image
```bash
docker build -t devops-info-service-python .
```

### Run Container
```bash
docker run -d -p 5000:5000 --name python-app timofeq1/devops-lab02-python:latest
```

### Pull from Docker Hub
```bash
docker pull timofeq1/devops-lab02-python:latest
docker run -d -p 5000:5000 timofeq1/devops-lab02-python:latest
```

## Testing

This project uses [pytest](https://docs.pytest.org/) for unit testing.

### Run Tests Locally

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Run with coverage:
   ```bash
   pytest --cov=. --cov-report=term-missing
   ```
