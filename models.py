from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate # Import Migrate
import os # Import os module

# 1. Create the Flask app instance
app = Flask(__name__)

# 2. Configure the app (BEFORE initializing extensions that need config)
#    Replace with your actual database URI
# Use the DATABASE_URL environment variable provided by Render
# Provide a default SQLite URI for local development if DATABASE_URL is not set
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Optional: Suppress a warning
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')

# 3. Initialize SQLAlchemy AFTER app configuration
db = SQLAlchemy()
bcrypt = Bcrypt()

db.init_app(app)
bcrypt.init_app(app)

# 4. Initialize Migrate AFTER app and db are created
migrate = Migrate(app, db) # Initialize Migrate

# --- Define your models AFTER db is initialized ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    resources = db.relationship('Resource', backref='author', lazy=True)
    date_joined = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    subject = db.Column(db.String(50), nullable=True)
    difficulty = db.Column(db.String(20), nullable=True)
    tags = db.Column(db.String(150), nullable=True)
    type = db.Column(db.String(20), nullable=True, default='Link')
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    progress = db.Column(db.String(50), nullable=False, default='Not Started')
    progress_percentage = db.Column(db.Integer, nullable=False, default=0)
    last_updated = db.Column(db.DateTime, nullable=True, onupdate=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    urls = db.relationship('ResourceURL', backref='resource', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"Resource('{self.title}')"

    def get_tags_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    def get_primary_url(self):
        """Get the primary URL for the resource"""
        primary_url = ResourceURL.query.filter_by(resource_id=self.id, is_primary=True).first()
        return primary_url.url if primary_url else None

class ResourceURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"ResourceURL('{self.url}', primary={self.is_primary})"

# --- Import or define your routes AFTER models and db are set up ---
# Example: from your_routes_file import *
# Or define routes directly here:
# @app.route('/')
# def index(): ...
