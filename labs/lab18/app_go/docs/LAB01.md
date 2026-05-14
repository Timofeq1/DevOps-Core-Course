# Lab 01 - Go Web Application

## Implementation Details
This bonus task implements the same service specification as the Python version but using Go's standard `net/http` package.

## API Documentation

### Main Endpoint
request:
```bash
curl http://localhost:8080/
```

### Health Check
request:
```bash
curl http://localhost:8080/health
```

## Compilation and Execution
```bash
go build -o app
./app
```
