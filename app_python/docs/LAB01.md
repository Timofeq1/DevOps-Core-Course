# Lab 01 - Python Web Application

## Framework Selection

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| Type | Microframework (Async) | Microframework | Full-stack |
| Performance | High (Starlette based) | Medium (WSGI) | Medium |
| Validation | Automatic (Pydantic) | Manual | Manual/DRF |
| Async | Native Support | Partial | Partial |

**Choice: FastAPI**
I chose FastAPI because it provides meaningful performance benefits through asynchronous support and offers automatic data validation and documentation generation (Swagger UI). It is modern, type-safe, and efficient for building microservices like this one.

## Best Practices Applied

1. **Clean Code Organization**
   - Import grouping (std lib, third party, local).
   - Functions with single responsibilities (`get_uptime`, `get_system_info`).
   - Docstrings for functions and endpoints.

2. **Configuration**
   - Use of environment variables for `HOST` and `PORT`.
   
   ```python
   host = os.getenv("HOST", "0.0.0.0")
   port = int(os.getenv("PORT", "5000"))
   ```

3. **Logging**
   - Configured standard logging middleware.
   
   ```python
   logging.basicConfig(level=logging.INFO, ...)
   logger.info("Processing request for /")
   ```

## API Documentation

### Main Endpoint
request:
```bash
curl http://localhost:5000/
```

### Health Check
request:
```bash
curl http://localhost:5000/health
```

## Challenges & Solutions

**Challenge:** Implementing accurate uptime calculation.
**Solution:** Initialized a global `START_TIME` variable when the application module is loaded and calculated the delta on each request.

**Challenge:** Handling platform specific information.
**Solution:** Used the standard `platform` library which provides cross-platform support for retrieving system details.

## GitHub Community
Starred the course repository and `simple-container-com/api`.
Followed the Professor and TAs.
Followed 3 classmates.
