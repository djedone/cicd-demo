from flask import Flask, jsonify, request, render_template
from app.database import db, init_db
from app.models import DeploymentLog
import os
import logging
from datetime import datetime
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import REGISTRY, CollectorRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)

metrics = None

def create_app(testing=False):
    """Application factory function"""
    app = Flask(__name__)
    
    # Konfiguracija
    if testing:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicijalizacija baze
    db.init_app(app)
    
    # Inicijalizacija metrika (samo ako nisu u testing modu)
    global metrics
    if os.getenv('ENABLE_METRICS', 'false').lower() == 'true' and not testing:
        metrics = PrometheusMetrics(app)
        # Custom metrike (registriraju se automatski kroz dekoratore)
        
        @metrics.counter(
            'deployment_total',
            'Total number of deployments',
            labels={'environment': lambda: request.view_args.get('env', 'unknown')}
        )
        def record_deployment_counter():
            pass  # Ovo je samo placeholder, pravo brojanje je u logici
    
    @app.before_request
    def initialize_database():
        if app.config.get('TESTING'):
            return
        try:
            with app.app_context():
                init_db()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            pass

    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"404 error for {request.url}")
        return jsonify({"error": "Not found", "message": str(error)}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {error}")
        return jsonify({"error": "Internal server error", "message": "Something went wrong"}), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return jsonify({"error": "Internal server error", "message": "An unexpected error occurred"}), 500

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/health")
    def health():
        """Health check endpoint"""
        try:
            # Proveri konekciju sa bazom
            db.session.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = f"unhealthy: {str(e)}"
        
        health_data = {
            "status": "UP",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "environment": os.getenv('ENVIRONMENT', 'development'),
            "version": "1.0.0"
        }
        
        logger.info(f"Health check: {health_data['status']}, Database: {db_status}")
        return jsonify(health_data), 200

    @app.route("/api/deployments", methods=["GET", "POST"])
    def deployments():
        """API za deployment logove"""
        if request.method == "POST":
            try:
                data = request.get_json()
                if data is None:
                    return jsonify({"error": "Invalid JSON"}), 400
            except Exception as e:
                return jsonify({"error": "Invalid JSON"}), 400
                
            version = data.get('version', 'unknown')
            environment = data.get('environment', 'unknown')
            
            # Spremi deployment u bazu
            try:
                log = DeploymentLog(
                    version=version,
                    environment=environment,
                    status="success",
                    deployed_at=datetime.utcnow()
                )
                db.session.add(log)
                db.session.commit()
                logger.info(f"Deployment recorded: {version} to {environment}")
                
                # Inkrementiraj metrike ako su omogućene
                if metrics:
                    from flask import current_app
                    with current_app.test_request_context():
                        record_deployment_counter()
                
                return jsonify({
                    "message": "Deployment recorded",
                    "version": version,
                    "environment": environment
                }), 201
            except Exception as e:
                logger.error(f"Failed to record deployment: {e}")
                return jsonify({"error": str(e)}), 500
        
        # GET method - vrati sve deployment logove
        try:
            logs = DeploymentLog.query.order_by(DeploymentLog.deployed_at.desc()).limit(10).all()
            
            return jsonify({
                "deployments": [{
                    "id": log.id,
                    "version": log.version,
                    "environment": log.environment,
                    "status": log.status,
                    "deployed_at": log.deployed_at.isoformat()
                } for log in logs]
            })
        except Exception as e:
            logger.error(f"Failed to retrieve deployments: {e}")
            return jsonify({"error": str(e), "deployments": []})

    @app.route("/metrics")
    def metrics_endpoint():
        """Prometheus metrics endpoint"""
        if metrics:
            from prometheus_client import generate_latest
            from flask import Response
            return Response(generate_latest(), mimetype='text/plain')
        return "Metrics disabled", 404

    @app.route("/api/stats")
    def stats():
        """Custom statistike za dashboard"""
        try:
            from sqlalchemy import func
            
            total_deployments = DeploymentLog.query.count()
            successful_deployments = DeploymentLog.query.filter_by(status="success").count()
            
            return jsonify({
                "total_deployments": total_deployments,
                "successful_deployments": successful_deployments,
                "success_rate": (successful_deployments / total_deployments * 100) if total_deployments > 0 else 0,
                "last_deployment": DeploymentLog.query.order_by(DeploymentLog.deployed_at.desc()).first().deployed_at.isoformat() if total_deployments > 0 else None
            })
        except Exception as e:
            logger.error(f"Failed to generate stats: {e}")
            return jsonify({"error": str(e)})

    @app.route("/api/metrics/custom")
    def custom_metrics():
        """Custom deployment metrics for dashboard"""
        try:
            from sqlalchemy import func, extract
            from datetime import datetime, timedelta
            
            # Get deployments from last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_deployments = DeploymentLog.query.filter(
                DeploymentLog.deployed_at >= thirty_days_ago
            ).all()
            
            # Calculate metrics
            total_recent = len(recent_deployments)
            successful_recent = len([d for d in recent_deployments if d.status == "success"])
            
            # Deployments by environment
            env_stats = db.session.query(
                DeploymentLog.environment,
                func.count(DeploymentLog.id).label('count')
            ).filter(
                DeploymentLog.deployed_at >= thirty_days_ago
            ).group_by(DeploymentLog.environment).all()
            
            # Calculate successful deployments for each environment
            env_data = []
            for env, count in env_stats:
                successful = DeploymentLog.query.filter(
                    DeploymentLog.environment == env,
                    DeploymentLog.status == 'success',
                    DeploymentLog.deployed_at >= thirty_days_ago
                ).count()
                env_data.append({
                    'environment': env,
                    'total': count,
                    'successful': successful
                })
            
            # Deployments by day (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            daily_stats = db.session.query(
                func.date(DeploymentLog.deployed_at).label('date'),
                func.count(DeploymentLog.id).label('count')
            ).filter(
                DeploymentLog.deployed_at >= seven_days_ago
            ).group_by(func.date(DeploymentLog.deployed_at)).all()
            
            return jsonify({
                "summary": {
                    "total_deployments_30d": total_recent,
                    "successful_deployments_30d": successful_recent,
                    "success_rate_30d": (successful_recent / total_recent * 100) if total_recent > 0 else 0,
                    "avg_deployments_per_day": total_recent / 30
                },
                "by_environment": [{
                    "environment": env['environment'],
                    "total": env['total'],
                    "successful": env['successful'],
                    "success_rate": (env['successful'] / env['total'] * 100) if env['total'] > 0 else 0
                } for env in env_data],
                "daily_deployments": [{
                    "date": str(date),
                    "count": count
                } for date, count in daily_stats],
                "generated_at": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to generate custom metrics: {e}")
            return jsonify({"error": str(e), "message": "Failed to generate custom metrics"})

    return app

# Create app instance for production
app = create_app(testing=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)