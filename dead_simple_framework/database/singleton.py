# MongoDB
from pymongo import MongoClient

# MongoDB Settings
from ..config import MongoDB_Settings

class MongoManager:
    ''' Singleton manager for MongoDB client '''

    __instance = None

    @staticmethod 
    def getInstance():
        if MongoManager.__instance == None:
            MongoManager()

        return MongoManager.__instance

    def __init__(self):
        if MongoManager.__instance != None:
            pass
        else:
            MongoManager.__instance = MongoClient(MongoDB_Settings.MONGODB_CONNECTION_STRING)
