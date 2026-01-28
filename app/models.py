from .database import db
from datetime import datetime

class DeploymentLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), nullable=False)
    environment = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, success, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'environment': self.environment,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }