# app/main.py
import os
from flask import Flask, jsonify, render_template, request
from app.database import db
from app.models import DeploymentLog
from prometheus_flask_exporter import PrometheusMetrics

def create_app():
    app = Flask(__name__)
    
    # Konfiguracija
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///local.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicijalizacija ekstenzija
    db.init_app(app)
    
    # Inicijalizacija Prometheus metrika
    metrics = PrometheusMetrics(app)
    
    # Custom metrika za broj deploymenta
    deployments_counter = metrics.counter(
        'deployments_total', 
        'Total number of deployments',
        labels={'status': lambda: request.status_code}
    )
    
    @app.route("/")
    def home():
        return render_template("index.html")
    
    @app.route("/health")
    def health():
        return jsonify(status="UP"), 200
    
    @app.route("/api/deployments", methods=["GET"])
    def get_deployments():
        deployments = DeploymentLog.query.order_by(DeploymentLog.deployed_at.desc()).limit(10).all()
        return jsonify([d.to_dict() for d in deployments])
    
    @app.route("/api/deployments", methods=["POST"])
    def create_deployment():
        data = request.get_json()
        deployment = DeploymentLog(
            version=data.get('version', '1.0.0'),
            status=data.get('status', 'success'),
            user=data.get('user', 'system'),
            commit_hash=data.get('commit_hash', ''),
            environment=data.get('environment', 'production')
        )
        db.session.add(deployment)
        db.session.commit()
        return jsonify(deployment.to_dict()), 201
    
    @app.route("/metrics")
    def metrics_endpoint():
        # Ova ruta je automatski dodana od strane PrometheusFlaskExporter
        pass
    
    @app.route("/api/metrics/custom")
    def custom_metrics():
        total_deployments = DeploymentLog.query.count()
        successful_deployments = DeploymentLog.query.filter_by(status='success').count()
        failed_deployments = DeploymentLog.query.filter_by(status='failed').count()
        
        return jsonify({
            'total_deployments': total_deployments,
            'successful_deployments': successful_deployments,
            'failed_deployments': failed_deployments,
            'success_rate': successful_deployments / total_deployments if total_deployments > 0 else 0
        })
    
    return app

# Kreiraj aplikaciju
app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Kreiraj tablice ako ne postoje
    app.run(host="0.0.0.0", port=5000)