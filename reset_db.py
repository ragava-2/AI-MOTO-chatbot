from app import app
from extensions import db
from database.models import User, Conversation, ChatHistory

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables...")
    db.create_all()
    print("Database reset complete! You can now start the server.")
