''' Database driver utilities '''

from flask import current_app, g
from flask_pymongo import PyMongo
from pymongo import MongoClient

# MongoDB Settings
from ..config import MongoDB_Settings

def get_mongo_instance():
    """
    Configuration method to return db instance
    """

    try:
        db = getattr(g, "_database", None)

        if db is None:

            db = g._database = PyMongo(current_app).db
        
        return db

    except RuntimeError as e:
        return MongoClient(MongoDB_Settings.MONGODB_CONNECTION_STRING).get_default_database()

