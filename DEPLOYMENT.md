# Deployment Guide

## Quick Deployment Options

### Docker Compose (Development)

```bash
git clone <repository-url>
cd cicd-demo
cp .env.example .env
docker-compose up -d
```

### Render.com (Production)

1. Create PostgreSQL service
2. Create web service with Docker runtime
3. Configure environment variables
4. Deploy

## Environment Configuration

### Required Variables

```bash
DATABASE_URL=postgresql://user:pass@host:5432/database
ENVIRONMENT=staging|production
ENABLE_METRICS=true
SECRET_KEY=<generated-secret-key>
```

### Generate Secret Keys

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Render.com Setup

### Database Service

1. Create PostgreSQL service
2. Note connection string
3. Use for both staging and production

### Web Services

#### Staging
- Name: cicd-demo-staging
- Runtime: Docker
- Branch: develop
- Auto-deploy: enabled

#### Production
- Name: cicd-demo-production
- Runtime: Docker
- Branch: main
- Auto-deploy: disabled (manual)

### Environment Variables

#### Staging
```
DATABASE_URL=<postgresql-connection-string>
ENVIRONMENT=staging
ENABLE_METRICS=true
SECRET_KEY=<staging-key>
```

#### Production
```
DATABASE_URL=<postgresql-connection-string>
ENVIRONMENT=production
ENABLE_METRICS=true
SECRET_KEY=<production-key>
```

## Production Docker Deployment

### Environment Setup

```bash
cp .env.example .env.production
# Edit with production values
```

### Deploy

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Services Included

- Application (port 5000)
- PostgreSQL (port 5432)
- Nginx reverse proxy (ports 80, 443)
- Prometheus (port 9090)
- Grafana (port 3000)

## CI/CD Pipeline

### GitHub Actions Configuration

Required secrets in GitHub repository:

```
RENDER_STAGING_DEPLOY_HOOK=https://api.render.com/deploy/srv-<id>/key
RENDER_PROD_DEPLOY_HOOK=https://api.render.com/deploy/srv-<id>/key
APPROVERS=<github-username>
```

### Deploy Hooks

1. Go to Render service settings
2. Find "Deploy Hooks" section
3. Copy webhook URLs
4. Add to GitHub Secrets

### Branch Strategy

- `main` → Production deployment
- `develop` → Staging deployment
- Manual approval required for production

## Monitoring

### Prometheus

- URL: http://localhost:9090
- Metrics endpoint: /metrics
- Key metrics: flask_http_request_total, deployment_total

### Grafana

- URL: http://localhost:3000
- Default credentials: admin/admin
- Dashboards: pre-configured

### Alerting

Alerts configured in monitoring/alerts.yml:
- Application down
- High error rate
- Performance issues

## Troubleshooting

### Database Connection

```bash
python3 scripts/simple_db_test.py
```

### Application Health

```bash
curl http://localhost:5000/health
```

### Check Logs

```bash
docker-compose logs app
```

### Render Deployment Issues

1. Check environment variables
2. Verify database connection
3. Review deployment logs
4. Test health endpoint

## Security Considerations

### SSL/TLS

1. Generate SSL certificates
2. Update nginx.conf
3. Configure HTTPS

### Rate Limiting

API endpoints rate-limited:
- `/api/*`: 10 requests/second
- Dashboard: 5 requests/second

### Security Headers

- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: "1; mode=block"

## Performance

### Scaling

```bash
# Scale application containers
docker-compose up -d --scale app=3
```

### Database Optimization

- Connection pooling
- Query optimization
- Indexing

### Monitoring

- Response time tracking
- Error rate monitoring
- Resource usage metrics

## Backup and Recovery

### Database Backup

```bash
docker-compose exec postgres pg_dump -U cicd_demo_user cicd_demo > backup.sql
```

### Grafana Backup

```bash
docker cp $(docker-compose ps -q grafana):/var/lib/grafana ./grafana-backup
```

## Maintenance

### Updates

```bash
git pull origin main
docker-compose build
docker-compose up -d
```

### Database Migrations

```bash
docker-compose exec app flask db upgrade
```

### Log Rotation

Configure log rotation for production:
- Application logs
- Nginx access logs
- Database logs
