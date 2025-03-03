from backend.models.database import Alert, Stock, db
from backend.services.stock_service import get_current_price
import logging
from datetime import datetime
import asyncio
import numpy as np

logger = logging.getLogger(__name__)

# Alert types
PRICE_ABOVE = "price_above"
PRICE_BELOW = "price_below"
VOLUME_ABOVE = "volume_above"
PERCENT_CHANGE = "percent_change"

# Function to convert NumPy values to Python native types
def convert_numpy_types(value):
    if isinstance(value, np.integer):
        return int(value)
    elif isinstance(value, np.floating):
        return float(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    return value

class AlertManager:
    """Manages the creation, checking, and triggering of alerts."""
    
    def __init__(self):
        self.triggered_alerts = []
        self._running = False
    
    async def start_monitoring(self, check_interval=60):
        """Start monitoring alerts in the background."""
        self._running = True
        while self._running:
            try:
                await self.check_all_alerts()
                await asyncio.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in alert monitoring: {str(e)}")
                await asyncio.sleep(check_interval)
    
    def stop_monitoring(self):
        """Stop the alert monitoring."""
        self._running = False
    
    async def check_all_alerts(self):
        """Check all active alerts."""
        try:
            active_alerts = Alert.select().where(Alert.is_active == True)
            for alert in active_alerts:
                await self.check_alert(alert)
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
    
    async def check_alert(self, alert):
        """Check if a specific alert should be triggered."""
        try:
            current_price = get_current_price(alert.stock.symbol)
            if current_price is None:
                return
                
            triggered = False
            
            if alert.alert_type == PRICE_ABOVE:
                triggered = current_price > alert.threshold_value
            elif alert.alert_type == PRICE_BELOW:
                triggered = current_price < alert.threshold_value
            elif alert.alert_type == VOLUME_ABOVE:
                # Would need to get volume data from stock service
                pass
            elif alert.alert_type == PERCENT_CHANGE:
                # Would need to calculate percent change
                pass
                
            if triggered:
                self.trigger_alert(alert, current_price)
        except Exception as e:
            logger.error(f"Error checking alert {alert.id}: {str(e)}")
    
    def trigger_alert(self, alert, current_value):
        """Trigger an alert by adding it to the triggered alerts list and updating DB."""
        try:
            # Update the alert in the database
            with db.atomic():
                alert.last_triggered = datetime.now()
                alert.save()
                
            # Convert NumPy values to Python native types
            current_value_native = convert_numpy_types(current_value)
                
            # Add to triggered alerts
            alert_data = {
                'id': alert.id,
                'stock_symbol': alert.stock.symbol,
                'stock_name': alert.stock.name,
                'alert_type': alert.alert_type,
                'threshold_value': alert.threshold_value,
                'current_value': current_value_native,
                'user_email': alert.user_email,
                'triggered_at': datetime.now()
            }
            self.triggered_alerts.append(alert_data)
            
            # Would typically send an email or notification here
            logger.info(f"Alert triggered: {alert_data}")
            
            return alert_data
        except Exception as e:
            logger.error(f"Error triggering alert {alert.id}: {str(e)}")
            return None
    
    def get_recent_triggered_alerts(self, limit=50):
        """Get recently triggered alerts."""
        return self.triggered_alerts[-limit:] if self.triggered_alerts else []
    
    def clear_triggered_alerts(self):
        """Clear the list of triggered alerts."""
        self.triggered_alerts = []

# Global alert manager instance
alert_manager = AlertManager()

def create_alert(stock_symbol, user_email, alert_type, threshold_value):
    """Create a new stock alert."""
    try:
        with db.atomic():
            stock = Stock.get(Stock.symbol == stock_symbol)
            
            # Convert threshold value to standard float in case it's a NumPy type
            threshold_value = convert_numpy_types(threshold_value)
            
            alert = Alert.create(
                stock=stock,
                user_email=user_email,
                alert_type=alert_type,
                threshold_value=float(threshold_value),
                is_active=True,
                created_at=datetime.now()
            )
            
            return {
                'id': alert.id,
                'stock_symbol': stock.symbol,
                'stock_name': stock.name,
                'alert_type': alert.alert_type,
                'threshold_value': convert_numpy_types(alert.threshold_value),
                'user_email': alert.user_email,
                'created_at': alert.created_at
            }
    except Stock.DoesNotExist:
        logger.error(f"Stock {stock_symbol} not found")
        return None
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        return None

def get_alerts_for_user(user_email):
    """Get all alerts for a specific user."""
    try:
        alerts = Alert.select().where(Alert.user_email == user_email)
        logger.info(f"Alerts for user {user_email}: {alerts}")
        return [
            {
                'id': alert.id,
                'stock_symbol': alert.stock.symbol,
                'stock_name': alert.stock.name,
                'alert_type': alert.alert_type,
                'threshold_value': convert_numpy_types(alert.threshold_value),
                'is_active': alert.is_active,
                'last_triggered': alert.last_triggered,
                'created_at': alert.created_at
            }
            for alert in alerts
        ]
    except Exception as e:
        logger.error(f"Error getting alerts for user {user_email}: {str(e)}")
        return []

def update_alert(alert_id, is_active=None, threshold_value=None):
    """Update an existing alert."""
    try:
        with db.atomic():
            alert = Alert.get_by_id(alert_id)
            
            if is_active is not None:
                alert.is_active = is_active
                
            if threshold_value is not None:
                # Convert threshold value to standard float
                threshold_value = convert_numpy_types(threshold_value)
                alert.threshold_value = float(threshold_value)
                
            alert.save()
            
            return {
                'id': alert.id,
                'stock_symbol': alert.stock.symbol,
                'stock_name': alert.stock.name,
                'alert_type': alert.alert_type,
                'threshold_value': convert_numpy_types(alert.threshold_value),
                'is_active': alert.is_active,
                'last_triggered': alert.last_triggered,
                'created_at': alert.created_at
            }
    except Alert.DoesNotExist:
        logger.error(f"Alert {alert_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error updating alert {alert_id}: {str(e)}")
        return None

def delete_alert(alert_id):
    """Delete an alert."""
    try:
        with db.atomic():
            alert = Alert.get_by_id(alert_id)
            alert.delete_instance()
            return True
    except Alert.DoesNotExist:
        logger.error(f"Alert {alert_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {str(e)}")
        return False 