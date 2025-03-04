from peewee import *
import datetime
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

# Define database - use environment variable for path if available
db_path = os.environ.get('DB_PATH', 'stock_screener.db')
db = SqliteDatabase(db_path)

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password_hash = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)
    last_login = DateTimeField(null=True)
    is_active = BooleanField(default=True)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Stock(BaseModel):
    symbol = CharField(unique=True)
    name = CharField()
    sector = CharField(null=True)
    industry = CharField(null=True)
    last_updated = DateTimeField(default=datetime.datetime.now)

class Alert(BaseModel):
    user = ForeignKeyField(User, backref='alerts')
    stock = ForeignKeyField(Stock, backref='alerts')
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
    
    # Drop all tables
    db.drop_tables([User, Stock, Alert, PriceHistory], safe=True)
    
    # Create tables with new schema
    db.create_tables([User, Stock, Alert, PriceHistory], safe=True)
    
    # Create a default admin user
    try:
        admin_user = User.create(
            username='admin',
            email='admin@example.com',
            is_active=True,
            created_at=datetime.datetime.now()
        )
        admin_user.set_password('admin123')  # Set a default password
        admin_user.save()
    except:
        pass  # User might already exist
    
    db.close()
