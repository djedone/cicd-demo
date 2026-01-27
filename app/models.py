# app/models.py
from .database import db
from datetime import datetime

class DeploymentLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(50), nullable=False)
    deployed_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False)  # success, failed, pending
    user = db.Column(db.String(100))
    commit_hash = db.Column(db.String(40))
    environment = db.Column(db.String(20), default='production')
    
    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'deployed_at': self.deployed_at.isoformat() if self.deployed_at else None,
            'status': self.status,
            'user': self.user,
            'commit_hash': self.commit_hash,
            'environment': self.environment
        }