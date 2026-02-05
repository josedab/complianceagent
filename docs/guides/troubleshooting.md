# Troubleshooting Guide

This guide covers common issues and their solutions when running ComplianceAgent.

## Quick Diagnostics

```bash
# Check all services status
make status

# View logs
make logs

# Run health check
curl http://localhost:8000/health
```

---

## Installation Issues

### Python Environment

#### Issue: `ModuleNotFoundError: No module named 'app'`

**Cause:** Virtual environment not activated or PYTHONPATH not set.

**Solution:**
```bash
cd backend
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Issue: `uv: command not found`

**Cause:** uv package manager not installed.

**Solution:**
```bash
pip install uv
# Or install directly with pip
cd backend && pip install -e ".[dev]"
```

#### Issue: Python version mismatch

**Cause:** Python < 3.12 installed.

**Solution:**
```bash
# Check version
python --version

# Install Python 3.12
# macOS
brew install python@3.12

# Ubuntu
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12 python3.12-venv
```

### Node.js Environment

#### Issue: `npm ERR! engine` incompatibility

**Cause:** Node.js version < 20.

**Solution:**
```bash
# Check version
node --version

# Install Node 20 via nvm
nvm install 20
nvm use 20
```

#### Issue: `EACCES: permission denied`

**Cause:** npm global permissions issue.

**Solution:**
```bash
# Fix npm permissions
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
export PATH=~/.npm-global/bin:$PATH
```

---

## Database Issues

### Connection Errors

#### Issue: `connection refused` to PostgreSQL

**Cause:** PostgreSQL not running or wrong port.

**Solution:**
```bash
# Check if running
docker ps | grep postgres

# Start infrastructure
make dev

# Verify connection
docker exec -it complianceagent-postgres-1 pg_isready
```

#### Issue: `password authentication failed`

**Cause:** Incorrect database credentials.

**Solution:**
```bash
# Check .env file
cat .env | grep DATABASE_URL

# Should be:
DATABASE_URL=postgresql+asyncpg://complianceagent:complianceagent@localhost:5432/complianceagent
```

#### Issue: `relation "xyz" does not exist`

**Cause:** Migrations not applied.

**Solution:**
```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

### Migration Errors

#### Issue: `Target database is not up to date`

**Cause:** Pending migrations exist.

**Solution:**
```bash
# Check current revision
alembic current

# Apply pending migrations
alembic upgrade head
```

#### Issue: `Can't locate revision`

**Cause:** Corrupted migration history.

**Solution:**
```bash
# Check migration history
alembic history

# If needed, stamp current state (use with caution)
alembic stamp head

# Regenerate migrations
alembic revision --autogenerate -m "fix migration"
```

---

## Redis Issues

#### Issue: `Connection refused` to Redis

**Cause:** Redis not running.

**Solution:**
```bash
# Check if running
docker ps | grep redis

# Start Redis
make dev

# Test connection
docker exec -it complianceagent-redis-1 redis-cli ping
# Should return: PONG
```

#### Issue: Celery workers not processing tasks

**Cause:** Workers not connected to Redis.

**Solution:**
```bash
# Check Redis URL in .env
cat .env | grep REDIS_URL

# Restart workers
make run-workers

# Check worker status
celery -A app.workers inspect active
```

---

## Elasticsearch Issues

#### Issue: `Connection refused` to Elasticsearch

**Cause:** Elasticsearch not running or still starting.

**Solution:**
```bash
# Check if running (may take 30-60 seconds to start)
docker ps | grep elasticsearch

# Check logs
docker logs complianceagent-elasticsearch-1

# Test connection
curl http://localhost:9200/_cluster/health
```

#### Issue: `index_not_found_exception`

**Cause:** Elasticsearch indices not created.

**Solution:**
```bash
# Create indices
python backend/scripts/setup_elasticsearch.py

# Or via API
curl -X PUT "localhost:9200/regulations"
```

#### Issue: Elasticsearch running out of memory

**Cause:** Insufficient heap size.

**Solution:**
```bash
# Check current memory
docker stats complianceagent-elasticsearch-1

# Increase memory in docker-compose.yml
environment:
  - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
```

---

## API Issues

### Authentication Errors

#### Issue: `401 Unauthorized` on all requests

**Cause:** Missing or invalid JWT token.

**Solution:**
```bash
# Get a new token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use token in subsequent requests
curl http://localhost:8000/api/v1/regulations \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Issue: `403 Forbidden` with valid token

**Cause:** Insufficient permissions.

**Solution:**
```bash
# Check user roles
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Contact admin to update permissions
```

### CORS Errors

#### Issue: `Access-Control-Allow-Origin` blocked

**Cause:** Frontend origin not in CORS allowed list.

**Solution:**
```bash
# Update .env
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Restart backend
make run-backend
```

### Rate Limiting

#### Issue: `429 Too Many Requests`

**Cause:** Rate limit exceeded.

**Solution:**
```bash
# Wait for rate limit window to reset (usually 1 minute)
# Or adjust rate limits in config (development only)

# Check current limits
curl -I http://localhost:8000/api/v1/regulations
# Look for X-RateLimit-* headers
```

---

## Frontend Issues

### Build Errors

#### Issue: `Module not found` in Next.js

**Cause:** Missing dependencies or incorrect imports.

**Solution:**
```bash
cd frontend
rm -rf node_modules .next
npm install
npm run build
```

#### Issue: TypeScript compilation errors

**Cause:** Type mismatches or missing types.

**Solution:**
```bash
# Check types
npm run type-check

# Generate types from API
npm run generate-types
```

### Runtime Errors

#### Issue: `Failed to fetch` API calls

**Cause:** Backend not running or CORS issue.

**Solution:**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check frontend environment
cat frontend/.env.local
# Should have:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Issue: Hydration mismatch errors

**Cause:** Server/client render mismatch.

**Solution:**
```bash
# Clear Next.js cache
rm -rf frontend/.next
npm run dev
```

---

## Docker Issues

### Container Startup

#### Issue: Containers keep restarting

**Cause:** Health check failures or configuration errors.

**Solution:**
```bash
# Check logs
docker logs complianceagent-backend-1

# Check health
docker inspect complianceagent-backend-1 | grep -A 10 Health
```

#### Issue: `port is already allocated`

**Cause:** Another service using the port.

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill process or use different port
# Update docker-compose.yml ports
```

### Volume Issues

#### Issue: Database data lost after restart

**Cause:** Volumes not persisted.

**Solution:**
```bash
# Verify volumes
docker volume ls | grep complianceagent

# Check docker-compose.yml has named volumes
volumes:
  postgres_data:
  redis_data:
```

---

## Performance Issues

### Slow API Responses

**Diagnosis:**
```bash
# Check database queries
# Enable SQL logging in .env
DATABASE_ECHO=true

# Check for N+1 queries in logs
```

**Solutions:**
1. Add database indexes
2. Use eager loading for relationships
3. Enable Redis caching

### High Memory Usage

**Diagnosis:**
```bash
# Check container memory
docker stats

# Check Python memory
pip install memory_profiler
python -m memory_profiler app/main.py
```

**Solutions:**
1. Reduce worker count
2. Enable connection pooling
3. Optimize batch processing

---

## Logging and Debugging

### Enable Debug Logging

```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart backend
make run-backend
```

### View Structured Logs

```bash
# Pretty print JSON logs
docker logs complianceagent-backend-1 2>&1 | jq .

# Filter by level
docker logs complianceagent-backend-1 2>&1 | jq 'select(.level == "error")'
```

### Debug Mode in VS Code

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Backend",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

---

## Getting Help

### Collect Diagnostic Information

```bash
# Generate diagnostic report
make diagnostics > diagnostics.txt

# Or manually:
echo "=== Environment ===" >> diagnostics.txt
cat .env | grep -v SECRET >> diagnostics.txt
echo "=== Docker ===" >> diagnostics.txt
docker ps -a >> diagnostics.txt
echo "=== Logs ===" >> diagnostics.txt
docker logs complianceagent-backend-1 --tail 100 >> diagnostics.txt
```

### Support Channels

- **GitHub Issues:** [github.com/complianceagent/issues](https://github.com/complianceagent/issues)
- **Documentation:** [docs.complianceagent.ai](https://docs.complianceagent.ai)
- **Community Discord:** [discord.gg/complianceagent](https://discord.gg/complianceagent)

### Before Reporting an Issue

1. Check this troubleshooting guide
2. Search existing GitHub issues
3. Collect diagnostic information
4. Include steps to reproduce
5. Include relevant log output (redact secrets!)

---

## Related Documentation

- [Development Setup](../development/README.md)
- [Configuration Reference](configuration.md)
- [Deployment Guide](../deployment/README.md)
