import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'myduka-pos-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///myduka_pos.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

