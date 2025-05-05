
from pymongo.mongo_client import MongoClient
from config.environments import settings
from constants.constants import db_models
from config.logger import logger


client = MongoClient(settings.MONGO_URL)

try:
    client.admin.command('ping')
    logger.info('Mongodb connected')
except Exception as e:
    print(e)

db = client.scraper
instagram_users = db[db_models["INSTAGRAM_USER"]]
instagram_posts = db[db_models["INSTAGRAM_POST"]]