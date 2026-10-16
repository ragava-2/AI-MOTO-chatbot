from flask import Flask, render_template
import os
from dotenv import load_dotenv
from datetime import timedelta

# Load env variables before importing local modules that rely on them
load_dotenv(override=True)

from extensions import db, bcrypt, jwt
from chatbot.routes import chatbot_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "this-is-a-very-long-development-secret-key-for-flask")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///chatbot.db")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

db.init_app(app)
bcrypt.init_app(app)
jwt.init_app(app)

app.register_blueprint(chatbot_bp, url_prefix="/api")

@app.route("/")
@app.route("/login")
@app.route("/register")
@app.route("/history")
def home():
    return render_template("index.html")

@app.route("/favicon.ico")
def favicon():
    return ("", 204)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
