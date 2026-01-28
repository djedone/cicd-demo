from flask import Flask, jsonify, request
from app.database import db
from app.models import DeploymentLog
import os
from datetime import datetime

def create_app(testing=False):
    """Application factory function"""
    app = Flask(__name__)
    
    # Configuration
    if testing:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'UP',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # API Routes
    @app.route('/api/deployments', methods=['GET'])
    def get_deployments():
        """Get all deployments"""
        deployments = DeploymentLog.query.order_by(DeploymentLog.created_at.desc()).all()
        return jsonify({
            'deployments': [{
                'id': d.id,
                'version': d.version,
                'environment': d.environment,
                'status': d.status,
                'created_at': d.created_at.isoformat()
            } for d in deployments]
        })
    
    @app.route('/api/deployments', methods=['POST'])
    def create_deployment():
        """Create a new deployment"""
        data = request.get_json()
        
        if not data or 'version' not in data or 'environment' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        deployment = DeploymentLog(
            version=data['version'],
            environment=data['environment'],
            status='pending'
        )
        
        db.session.add(deployment)
        db.session.commit()
        
        return jsonify({
            'id': deployment.id,
            'version': deployment.version,
            'environment': deployment.environment,
            'status': deployment.status,
            'created_at': deployment.created_at.isoformat()
        }), 201
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(error):
        app.logger.error(f'Server error: {error}')
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

# Create app instance for production
app = create_app(testing=False)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)