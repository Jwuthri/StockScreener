import datetime

import bcrypt
from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker

load_dotenv()

POSTGRES_DATABASE_NAME = "stock_screener"
POSTGRES_DATABASE_PASSWORD = "postgres"
POSTGRES_DATABASE_URL = "127.0.0.1:5432"
POSTGRES_DATABASE_USERNAME = "postgres"
DATABASE_URI = f"postgresql://:{POSTGRES_DATABASE_PASSWORD}:{POSTGRES_DATABASE_PASSWORD}@{POSTGRES_DATABASE_URL}/{POSTGRES_DATABASE_NAME}"

engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

# Create base model
Base = declarative_base()
Base.query = db_session.query_property()


# Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.datetime.now)
    # Relationships
    alerts = relationship("Alert", back_populates="user")
    taken_trades = relationship("TakenTrade", back_populates="user")

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    name = Column(String)
    description = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    exchange = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.now)

    # Relationships
    alerts = relationship("Alert", back_populates="stock")
    price_history = relationship("PriceHistory", back_populates="stock")
    taken_trades = relationship("TakenTrade", back_populates="stock")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    alert_type = Column(String)  # price_above, price_below, volume_above, etc.
    threshold_value = Column(Float)
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.now)

    # Relationships
    user = relationship("User", back_populates="alerts")
    stock = relationship("Stock", back_populates="alerts")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    timeframe = Column(String)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    date = Column(String)

    created_at = Column(DateTime, default=datetime.datetime.now)

    # Relationships
    stock = relationship("Stock", back_populates="price_history")


class TakenTrade(Base):
    __tablename__ = "taken_trades"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Trade details
    strategy_name = Column(String)  # Name of the strategy that took the trade
    entry_timestamp = Column(DateTime)  # When the trade was taken
    entry_price = Column(Float)  # Price at which we entered
    prev_day_high = Column(Float)  # Previous day's high price
    target_price = Column(Float)  # Target price that triggered the trade
    shares = Column(Integer)  # Number of shares bought
    total_cost = Column(Float)  # Total cost of the position
    position_size_percentage = Column(Float)  # Percentage of account used

    # Trade status
    is_open = Column(Boolean, default=True)  # Whether the trade is still open
    exit_timestamp = Column(DateTime, nullable=True)  # When we exited the trade
    exit_price = Column(Float, nullable=True)  # Price at which we exited
    profit_loss = Column(Float, nullable=True)  # Realized P/L
    profit_loss_percentage = Column(Float, nullable=True)  # Realized P/L as percentage

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # Relationships
    stock = relationship("Stock", back_populates="taken_trades")
    user = relationship("User", back_populates="taken_trades")


# Get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_db():
    """Initialize database and create tables if they don't exist."""
    # Create tables - in production, use Alembic migrations instead
    # Base.metadata.create_all(bind=engine)

    # Create a default admin user
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin", email="admin@example.com", is_active=True, created_at=datetime.datetime.now()
            )
            admin_user.set_password("admin123")  # Set a default password
            db.add(admin_user)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
    finally:
        db.close()


# if __name__ == "__main__":
#     initialize_db()
