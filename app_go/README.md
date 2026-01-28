# DevOps Info Service (Go)

## Overview
A production-ready Go web service that provides comprehensive system information and health monitoring.

## Prerequisites
- Go 1.21+

## Building the Application

1. Compile the code:
   ```bash
   go build -o app
   ```

## Running the Application

Standard run:
```bash
./app
```
The application will start on port 8080 by default.

Custom configuration:
```bash
PORT=9090 ./app
```

## API Endpoints

### GET /
Returns service metadata and system information.

### GET /health
Returns health status and uptime.
