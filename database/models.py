from extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with Conversations
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade="all, delete-orphan")

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False, default="New Conversation")
    vehicle_type = db.Column(db.String(20), nullable=False, default="bike") # "bike" or "car"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key to User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship with ChatHistory
    messages = db.relationship('ChatHistory', backref='conversation', lazy=True, cascade="all, delete-orphan")

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key to Conversation
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)

class VehicleKnowledge(db.Model):
    """
    Scalable vehicle knowledge schema supporting exact matching of:
    - Vehicle type (bike or car)
    - Manufacturer / brand
    - Exact model & model aliases
    - Model year or year range
    - Vehicle component & component aliases
    - Verified component and vehicle images & specifications
    """
    __tablename__ = 'vehicle_knowledge'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_type = db.Column(db.String(20), nullable=False, index=True) # 'bike' or 'car'
    manufacturer = db.Column(db.String(80), nullable=False, index=True) # e.g. 'Yamaha', 'BMW'
    model = db.Column(db.String(120), nullable=False, index=True) # e.g. 'YZF-R15 V4'
    model_aliases = db.Column(db.JSON, nullable=True) # e.g. ['R15 V4', 'R15M', 'YZF R15 V4']
    year_start = db.Column(db.Integer, nullable=True) # e.g. 2021
    year_end = db.Column(db.Integer, nullable=True) # e.g. 2025 (or None if current)
    component_name = db.Column(db.String(120), nullable=True, index=True) # None for vehicle overview, or 'Spark Plug'
    component_aliases = db.Column(db.JSON, nullable=True) # e.g. ['sparkplug', 'plug', 'ignition plug']
    specifications = db.Column(db.JSON, nullable=True) # Key-value specs dict
    image_path = db.Column(db.String(255), nullable=True) # Local path e.g. '/static/images/vehicles/yamaha_r15.jpg'
    image_source = db.Column(db.String(50), default="local_verified") # 'local_verified', 'live_search'
    verified = db.Column(db.Boolean, default=True, nullable=False)
    confidence = db.Column(db.Float, default=1.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_type": self.vehicle_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "model_aliases": self.model_aliases or [],
            "year_start": self.year_start,
            "year_end": self.year_end,
            "component_name": self.component_name,
            "component_aliases": self.component_aliases or [],
            "specifications": self.specifications or {},
            "image_path": self.image_path,
            "image_source": self.image_source,
            "verified": self.verified,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

