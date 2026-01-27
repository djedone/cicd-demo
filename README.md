# CI/CD Demo za Magistarski Rad

A comprehensive CI/CD pipeline demonstration with multi-environment deployment, security scanning, monitoring, and real-time analytics dashboard.

## 🚀 Features

### Core Application
- **Flask Web Application** with RESTful API
- **PostgreSQL Database** integration with SQLAlchemy ORM
- **Real-time Dashboard** with live metrics and charts
- **Deployment Logging** and analytics
- **Prometheus Metrics** integration

### CI/CD Pipeline
- **Multi-stage Docker builds** for optimized images
- **Automated Testing** with pytest and coverage reporting
- **Security Scanning** (Bandit SAST, Safety dependency checks, Trivy container scanning)
- **Multi-environment Deployment** (Staging/Production)
- **Performance Testing** with Locust load testing
- **Automated Deployments** with manual approval for production

### Monitoring & Observability
- **Prometheus** metrics collection
- **Grafana** dashboards and visualization
- **Custom Alerting** rules for proactive monitoring
- **Comprehensive Logging** with structured output
- **Health Checks** and status endpoints
- **Performance Benchmarks** and monitoring

### Infrastructure
- **Docker Compose** for local development
- **Production-ready** Docker setup with Nginx reverse proxy
- **Render.com** deployment configuration
- **Environment-specific** configurations
- **Security hardening** with rate limiting and headers

## 📊 API Endpoints

### Core Endpoints
- `GET /` - Interactive dashboard with real-time metrics
- `GET /health` - Health check with database status
- `GET /metrics` - Prometheus metrics endpoint

### Deployment API
- `GET /api/deployments` - List recent deployments (limit 10)
- `POST /api/deployments` - Create deployment log
  ```json
  {
    "version": "1.0.0",
    "environment": "production"
  }
  ```

### Analytics API
- `GET /api/stats` - Basic deployment statistics
- `GET /api/metrics/custom` - Comprehensive analytics with:
  - 30-day deployment summary
  - Environment distribution
  - Daily deployment trends
  - Success rates and averages

## 🛠️ Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL (optional, Docker image provided)

### Local Development

1. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd cicd-demo
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```
   The application will be available at `http://localhost:5000`

3. **Run tests**
   ```bash
   docker-compose exec app python -m pytest
   ```

4. **Run performance tests**
   ```bash
   docker-compose exec app python scripts/performance_test.py
   ```

### Manual Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup database**
   ```bash
   # Start PostgreSQL
   docker run -d --name postgres \
     -e POSTGRES_DB=cicd_demo \
     -e POSTGRES_USER=cicd_demo_user \
     -e POSTGRES_PASSWORD=localpass \
     -p 5432:5432 postgres:15
   ```

3. **Run the application**
   ```bash
   export DATABASE_URL="postgresql://cicd_demo_user:localpass@localhost:5432/cicd_demo"
   export ENABLE_METRICS="true"
   python app/main.py
   ```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_app.py
```

### Integration Tests
```bash
# Run comprehensive integration tests
pytest tests/test_integration.py -v
```

### Performance Testing
```bash
# Quick performance benchmark
python scripts/performance_test.py --benchmark-only

# Full load testing
python scripts/performance_test.py --users 20 --duration 60

# Test specific endpoint
python scripts/performance_test.py --endpoint /api/stats
```

### Load Testing with Locust
```bash
# Start the application
python app/main.py &

# Run load tests
locust -f scripts/load_test.py --headless \
  -u 10 -r 2 --run-time 60s --host http://localhost:5000
```

## 🚀 Deployment

### Render.com Deployment

1. **Setup Render account** and create new web service
2. **Connect repository** and configure build settings
3. **Set environment variables** from `.env.example`
4. **Configure database** (Render PostgreSQL)
5. **Deploy** - automatic CI/CD pipeline will run

### Production Docker Deployment

1. **Setup environment**
   ```bash
   cp .env.example .env.production
   # Edit production configuration
   ```

2. **Deploy with production compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Setup monitoring**
   ```bash
   # Grafana will be available at http://localhost:3000
   # Prometheus at http://localhost:9090
   ```

## 📈 Monitoring

### Grafana Dashboard
- **URL**: `http://localhost:3000` (production)
- **Default credentials**: admin/admin (change on first login)
- **Pre-configured dashboards** for application metrics

### Prometheus Metrics
- **URL**: `http://localhost:9090` (production)
- **Key metrics**:
  - `flask_http_request_total` - Request count
  - `flask_http_request_duration_seconds` - Response times
  - `deployment_total` - Deployment count
  - `deployment_success_rate` - Success percentage

### Alerting
Alerts are configured in `monitoring/alerts.yml`:
- **Application down** alerts
- **High error rate** notifications
- **Performance degradation** warnings
- **Database connection** issues

## 🔧 Configuration

### Environment Variables
```bash
# Application
ENVIRONMENT=development
FLASK_ENV=development
DEBUG=true

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Metrics
ENABLE_METRICS=true

# Security
SECRET_KEY=your-secret-key
```

### Docker Configuration
- **Multi-stage builds** for optimized image size
- **Health checks** for container monitoring
- **Resource limits** for production stability
- **Security scanning** in CI pipeline

## 📊 CI/CD Pipeline Metrics

- **Build Time**: ~2 minutes
- **Test Coverage**: > 80%
- **Security Issues**: Critical: 0, High: 0
- **Deployment Frequency**: Multiple times per day
- **Success Rate**: > 95%
- **Performance**: < 100ms average response time

## 🔒 Security Features

- **SAST scanning** with Bandit
- **Dependency scanning** with Safety
- **Container scanning** with Trivy
- **Security headers** via Nginx
- **Rate limiting** for API protection
- **Environment variable** protection
- **Secret management** best practices

## 📝 Project Structure

```
cicd-demo/
├── app/                    # Flask application
│   ├── main.py            # Main application file
│   ├── models.py          # Database models
│   ├── database.py        # Database configuration
│   └── templates/         # HTML templates
├── tests/                 # Test suite
│   ├── test_app.py        # Unit tests
│   ├── test_integration.py # Integration tests
│   └── conftest.py        # Test configuration
├── scripts/               # Utility scripts
│   ├── load_test.py       # Locust load testing
│   └── performance_test.py # Performance benchmarks
├── monitoring/            # Monitoring configuration
│   ├── alerts.yml         # Prometheus alerting rules
│   └── grafana/           # Grafana dashboards
├── .github/workflows/     # GitHub Actions CI/CD
├── docker-compose.yml     # Development environment
├── docker-compose.prod.yml # Production environment
├── dockerfile            # Docker image definition
├── render.yaml           # Render deployment config
├── nginx.conf            # Nginx configuration
├── prometheus.yml        # Prometheus configuration
└── requirements.txt       # Python dependencies
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎓 Academic Use

This project was developed as a master's thesis demonstration of:
- Modern CI/CD practices
- DevOps monitoring and observability
- Cloud-native application development
- Security in the software development lifecycle

## 🔗 Links

- **Live Demo**: [Application Dashboard](http://localhost:5000)
- **Monitoring**: [Grafana](http://localhost:3000) | [Prometheus](http://localhost:9090)
- **Documentation**: [API Docs](http://localhost:5000/health)
- **Repository**: [GitHub Repository](https://github.com/your-username/cicd-demo)

---

**Note**: This is a demonstration project for academic purposes. For production use, ensure proper security hardening and configuration.