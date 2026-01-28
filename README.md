# Master Thesis Demo

This repository contains the demonstration application for my Master's Thesis, showcasing CI/CD practices.

## Features

- Flask web application with REST API
- PostgreSQL database with SQLAlchemy ORM
- Docker-based deployment
- Basic monitoring with Prometheus

## Quick Start

1. Clone the repository
2. Set up environment variables in `.env`
3. Run with Docker:
   ```bash
   docker-compose up --build
   ```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m flask run
```

## Testing

```bash
pytest
```

### Local Development

1. Clone repository
```bash
git clone <repository-url>
cd cicd-demo
cp .env.example .env
```

2. Start with Docker
```bash
docker-compose up -d
```

3. Run tests
```bash
docker-compose exec app python -m pytest
```

### Manual Setup

1. Install dependencies
```bash
pip install -r requirements.txt
```

2. Setup database
```bash
docker run -d --name postgres \
  -e POSTGRES_DB=cicd_demo \
  -e POSTGRES_USER=cicd_demo_user \
  -e POSTGRES_PASSWORD=localpass \
  -p 5432:5432 postgres:15
```

3. Run application
```bash
export DATABASE_URL="postgresql://cicd_demo_user:localpass@localhost:5432/cicd_demo"
export ENABLE_METRICS="true"
python app/main.py
```

## Testing

### Unit Tests
```bash
pytest
pytest --cov=app
pytest tests/test_app.py
```

### Integration Tests
```bash
pytest tests/test_integration.py
```

### Performance Testing
```bash
python scripts/performance_test.py
locust -f scripts/load_test.py --headless -u 10 -r 2 --run-time 60s
```

## Deployment

### Render.com

#### Staging Environment
1. Create web service with Docker runtime
2. Set environment variables:
```
DATABASE_URL=postgresql://user:pass@host:5432/db
ENVIRONMENT=staging
ENABLE_METRICS=true
SECRET_KEY=<generated-key>
```

#### Production Environment
1. Create web service with Docker runtime
2. Set environment variables:
```
DATABASE_URL=postgresql://user:pass@host:5432/db
ENVIRONMENT=production
ENABLE_METRICS=true
SECRET_KEY=<different-generated-key>
```

### Production Docker

1. Configure environment
```bash
cp .env.example .env.production
```

2. Deploy
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring

### Prometheus
- URL: http://localhost:9090
- Metrics: flask_http_request_total, flask_http_request_duration_seconds

### Grafana
- URL: http://localhost:3000
- Default: admin/admin
- Pre-configured dashboards included

### Alerting
Alerts configured in monitoring/alerts.yml:
- Application downtime
- High error rates
- Performance degradation

## Configuration

### Environment Variables
```bash
ENVIRONMENT=development
DATABASE_URL=postgresql://user:pass@host:5432/db
ENABLE_METRICS=true
SECRET_KEY=your-secret-key
```

### Docker
- Multi-stage builds
- Health checks
- Security scanning in CI

## Security

- SAST scanning with Bandit
- Dependency scanning with Safety
- Container scanning with Trivy
- Rate limiting
- Security headers

## Project Structure

```
cicd-demo/
├── app/                    # Flask application
│   ├── main.py            # Main application
│   ├── models.py          # Database models
│   ├── database.py        # Database config
│   └── templates/         # HTML templates
├── tests/                 # Test suite
├── scripts/               # Utility scripts
├── monitoring/            # Monitoring config
├── .github/workflows/     # CI/CD pipeline
├── docker-compose.yml     # Development
├── docker-compose.prod.yml # Production
├── dockerfile            # Docker image
├── render.yaml           # Render config
└── requirements.txt       # Dependencies
```

## CI/CD Pipeline

### GitHub Actions Workflow

1. **Build & Test**
   - Python 3.11 setup
   - Dependency installation
   - Unit and integration tests
   - Coverage reporting

2. **Security Scanning**
   - Bandit SAST
   - Safety dependency check
   - Trivy container scan

3. **Deployment**
   - Docker build
   - Staging deploy (develop branch)
   - Production deploy (main branch with approval)

### Branch Strategy
- `main` → Production
- `develop` → Staging
- `feature/*` → No deployment

## License

MIT License