import firebase_admin
import redis as redis_client
from firebase_admin import credentials, storage, db as firebase_db
from decouple import config
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateRedisStorage
from telebot.types import LabeledPrice, ShippingOption

BOT_TOKEN = config('BOT_TOKEN')
DATABASE_URL = config('DATABASE_URL')
FIREBASE_CERTIFICATE = config('FIREBASE_CERTIFICATE')
REDIS_HOST = config('REDIS_HOST')
REDIS_PORT = config('REDIS_PORT')
STORAGE_BUCKET = config('STORAGE_BUCKET')
GITHUB_ACCESS = config('GITHUB_ACCESS')
PROJECT_ID = 'telegram-bot-1-c1cfe'
HOST = config('HOST', 'https://34.32.40.27')

prices = [LabeledPrice(label='Working Time Machine', amount=5750), LabeledPrice('Gift wrapping', 500)]

shipping_options = [
    ShippingOption(id='instant', title='WorldWide Teleporter').add_price(LabeledPrice('Teleporter', 1000)),
    ShippingOption(id='pickup', title='Local pickup').add_price(LabeledPrice('Pickup', 300))]

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

state_storage = StateRedisStorage(REDIS_HOST, REDIS_PORT)


BOT = AsyncTeleBot(BOT_TOKEN, state_storage=state_storage)

