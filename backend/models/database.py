from peewee import *
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Define database - use environment variable for path if available
db_path = os.environ.get('DB_PATH', 'stock_screener.db')
db = SqliteDatabase(db_path)

class BaseModel(Model):
    class Meta:
        database = db

class Stock(BaseModel):
    symbol = CharField(unique=True)
    name = CharField()
    sector = CharField(null=True)
    industry = CharField(null=True)
    last_updated = DateTimeField(default=datetime.datetime.now)

class Alert(BaseModel):
    stock = ForeignKeyField(Stock, backref='alerts')
    user_email = CharField()
    alert_type = CharField()  # price_above, price_below, volume_above, etc.
    threshold_value = FloatField()
    is_active = BooleanField(default=True)
    last_triggered = DateTimeField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

class PriceHistory(BaseModel):
    stock = ForeignKeyField(Stock, backref='price_history')
    timestamp = DateTimeField()
    open = FloatField()
    high = FloatField()
    low = FloatField()
    close = FloatField()
    volume = IntegerField()

def initialize_db():
    """Initialize database and create tables if they don't exist."""
    db.connect()
    db.create_tables([Stock, Alert, PriceHistory], safe=True)
    db.close()
