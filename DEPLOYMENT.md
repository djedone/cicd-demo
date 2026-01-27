# Deployment Guide

This guide covers various deployment options for the CI/CD Demo application.

## 🚀 Quick Deployment Options

### 1. Docker Compose (Recommended for Development)

```bash
# Clone and setup
git clone <repository-url>
cd cicd-demo
cp .env.example .env

# Start all services
docker-compose up -d

# Access the application
open http://localhost:5000
```

### 2. Render.com (Recommended for Production)

1. **Create Render Account**
   - Sign up at [render.com](https://render.com)
   - Connect your GitHub repository

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your repository
   - Use the following settings:
     - **Runtime**: Docker
     - **Build Command**: `docker build -t cicd-demo .`
     - **Start Command**: `gunicorn --bind 0.0.0.0:5000 --workers 2 app.main:app`

3. **Add Environment Variables**
   ```
   ENVIRONMENT=production
   DATABASE_URL=postgresql://...
   ENABLE_METRICS=true
   SECRET_KEY=your-secret-key
   ```

4. **Create PostgreSQL Database**
   - Click "New +" → "PostgreSQL"
   - Use the connection string in your web service

5. **Deploy**
   - Push to `main` branch for automatic deployment

### 3. Manual Docker Deployment

```bash
# Build the image
docker build -t cicd-demo .

# Run with PostgreSQL
docker run -d --name postgres \
  -e POSTGRES_DB=cicd_demo \
  -e POSTGRES_USER=cicd_demo_user \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 postgres:15

# Run the application
docker run -d --name cicd-demo \
  --link postgres \
  -e DATABASE_URL=postgresql://cicd_demo_user:secure_password@postgres:5432/cicd_demo \
  -e ENABLE_METRICS=true \
  -p 5000:5000 cicd-demo
```

## 🔧 Production Configuration

### Environment Variables

Create a `.env.production` file with:

```bash
# Production Settings
ENVIRONMENT=production
FLASK_ENV=production
DEBUG=false

# Database (use Render PostgreSQL or your own)
DATABASE_URL=postgresql://user:password@host:5432/database

# Security
SECRET_KEY=your-very-secure-secret-key-here

# Metrics
ENABLE_METRICS=true

# Logging
LOG_LEVEL=WARNING
```

### Production Docker Compose

Use `docker-compose.prod.yml` for production:

```bash
# Set required environment variables
export DB_PASSWORD=your-secure-password
export SECRET_KEY=your-secret-key
export GRAFANA_PASSWORD=your-grafana-password

# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d
```

This includes:
- **Application** with health checks
- **PostgreSQL** database with persistence
- **Nginx** reverse proxy with SSL support
- **Prometheus** metrics collection
- **Grafana** visualization dashboard

## 🔒 Security Considerations

### SSL/TLS Setup

1. **Generate SSL certificates** (for production):
   ```bash
   # Use Let's Encrypt or your organization's certificates
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout ssl/key.pem -out ssl/cert.pem
   ```

2. **Update Nginx configuration**:
   ```nginx
   server {
       listen 443 ssl http2;
       server_name your-domain.com;
       
       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;
       # ... rest of SSL config
   }
   ```

### Security Headers

The Nginx configuration includes:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: "1; mode=block"
- Strict-Transport-Security (when SSL is enabled)

### Rate Limiting

API endpoints are rate-limited:
- `/api/*`: 10 requests/second
- Dashboard: 5 requests/second
- Health checks: No rate limiting

## 📊 Monitoring Setup

### Prometheus Configuration

1. **Access Prometheus**: `http://localhost:9090`
2. **Key metrics to monitor**:
   - `flask_http_request_total`
   - `flask_http_request_duration_seconds`
   - `deployment_total`
   - `deployment_success_rate`

### Grafana Dashboard

1. **Access Grafana**: `http://localhost:3000`
2. **Login**: admin/admin (change immediately)
3. **Import dashboards** from `monitoring/grafana/`

### Alerting

Alerts are configured in `monitoring/alerts.yml`:
- Application downtime
- High error rates
- Performance degradation
- Database connection issues

Set up alert notifications in `prometheus.yml`:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

## 🔄 CI/CD Pipeline

### GitHub Actions

The pipeline includes:

1. **Build & Test**
   - Python 3.11 setup
   - Dependency installation
   - Unit and integration tests
   - Coverage reporting

2. **Security Scanning**
   - Bandit SAST scanning
   - Safety dependency checks
   - Trivy container scanning

3. **Performance Testing**
   - Locust load testing
   - Performance benchmarks

4. **Deployment**
   - Docker image build
   - Staging deployment (develop branch)
   - Production deployment (main branch with approval)

### Branch Strategy

- **`main`**: Production deployments
- **`develop`**: Staging deployments
- **feature/***: Feature branches (no deployment)

### Deployment Secrets

Configure these in GitHub repository settings:

```
RENDER_STAGING_DEPLOY_HOOK=https://api.render.com/deploy/srv-xxxxx/key
RENDER_PROD_DEPLOY_HOOK=https://api.render.com/deploy/srv-yyyy/key
APPROVERS=your-github-username
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check PostgreSQL status
   docker-compose ps postgres
   
   # Check logs
   docker-compose logs postgres
   
   # Test connection
   docker-compose exec app python -c "from app.database import db; print(db.engine.execute('SELECT 1').scalar())"
   ```

2. **Application Not Starting**
   ```bash
   # Check application logs
   docker-compose logs app
   
   # Check health endpoint
   curl http://localhost:5000/health
   ```

3. **High Memory Usage**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Restart services if needed
   docker-compose restart app
   ```

4. **Metrics Not Available**
   ```bash
   # Check if metrics are enabled
   curl http://localhost:5000/metrics
   
   # Verify Prometheus configuration
   curl http://localhost:9090/targets
   ```

### Performance Issues

1. **Slow Database Queries**
   - Check PostgreSQL logs
   - Monitor connection pool
   - Consider adding indexes

2. **High Response Times**
   - Check application logs
   - Monitor CPU/memory usage
   - Scale horizontally if needed

3. **Load Test Failures**
   - Reduce concurrent users
   - Check resource limits
   - Optimize database queries

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale application containers
docker-compose up -d --scale app=3

# Use load balancer (Nginx handles this automatically)
```

### Database Scaling

- **Read replicas**: Set up PostgreSQL read replicas
- **Connection pooling**: Use PgBouncer for connection management
- **Caching**: Add Redis for application caching

### Monitoring Scaling

- **Prometheus**: Add remote write for long-term storage
- **Grafana**: Configure persistent storage
- **Alerting**: Set up multiple alert managers

## 🔄 Updates and Maintenance

### Application Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d
```

### Database Migrations

```bash
# Run migrations (if using Flask-Migrate)
docker-compose exec app flask db upgrade
```

### Backup Strategy

```bash
# Database backup
docker-compose exec postgres pg_dump -U cicd_demo_user cicd_demo > backup.sql

# Grafana dashboards backup
docker cp $(docker-compose ps -q grafana):/var/lib/grafana ./grafana-backup
```

## 📞 Support

For deployment issues:

1. Check the troubleshooting section
2. Review application logs
3. Verify environment variables
4. Test individual components

For production deployments, consider:
- Setting up log aggregation
- Configuring backup monitoring
- Implementing disaster recovery
- Regular security updates
