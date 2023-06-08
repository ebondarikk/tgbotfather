import firebase_admin
import redis as redis_client
from firebase_admin import credentials, storage, db as firebase_db
from decouple import config

BOT_TOKEN = config('BOT_TOKEN')
DATABASE_URL = config('DATABASE_URL')
FIREBASE_CERTIFICATE = config('FIREBASE_CERTIFICATE')
REDIS_HOST = config('REDIS_HOST')
REDIS_PORT = config('REDIS_PORT')
STORAGE_BUCKET = config('STORAGE_BUCKET')
PROJECT_ID = 'telegram-bot-1-c1cfe'

redis = redis_client.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

cred = credentials.Certificate(FIREBASE_CERTIFICATE)
firebase_admin.initialize_app(
    cred,
    {
        'storageBucket': STORAGE_BUCKET,
        'databaseURL': DATABASE_URL
    }
)
bucket = storage.bucket()
db = firebase_db.reference()
