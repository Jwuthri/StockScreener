from backend.models.database import Alert, Stock, User, db_session as db
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
            active_alerts = db.query(Alert).filter(Alert.is_active == True).all()
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
            alert.last_triggered = datetime.now()
            db.commit()
            
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
                'user_email': alert.user.email,
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

def create_alert(stock_symbol: str, user: User, alert_type: str, threshold_value: float):
    """Create a new alert for a user"""
    try:
        # Convert threshold_value to Python native type if needed
        threshold_value = convert_numpy_types(threshold_value)
        
        # Find the stock
        stock = db.query(Stock).filter(Stock.symbol == stock_symbol).first()
        if not stock:
            return {"success": False, "message": f"Stock {stock_symbol} not found"}
        
        # Create the alert
        alert = Alert(
            user_id=user.id,
            stock_id=stock.id,
            alert_type=alert_type,
            threshold_value=threshold_value,
            is_active=True,
            created_at=datetime.now()
        )
        
        db.add(alert)
        db.commit()
        
        return {
            "success": True,
            "message": f"Alert created for {stock_symbol}",
            "alert_id": alert.id
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating alert: {str(e)}")
        return {"success": False, "message": f"Failed to create alert: {str(e)}"}

def get_alerts_for_user(user: User):
    """Get all alerts for a user"""
    try:
        alerts = db.query(Alert).join(Stock).filter(Alert.user_id == user.id).all()
        
        alerts_data = []
        for alert in alerts:
            # Get current price for comparison
            current_price = get_current_price(alert.stock.symbol)
            
            alerts_data.append({
                "id": alert.id,
                "stock_symbol": alert.stock.symbol,
                "stock_name": alert.stock.name,
                "alert_type": alert.alert_type,
                "threshold_value": alert.threshold_value,
                "current_value": current_price,
                "is_active": alert.is_active,
                "last_triggered": alert.last_triggered,
                "created_at": alert.created_at
            })
        
        return {"success": True, "alerts": alerts_data}
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return {"success": False, "message": f"Failed to get alerts: {str(e)}"}

def update_alert(alert_id: int, is_active: bool = None, threshold_value: float = None):
    """Update an alert's status or threshold value"""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return {"success": False, "message": f"Alert with ID {alert_id} not found"}
        
        # Update fields if provided
        if is_active is not None:
            alert.is_active = is_active
        
        if threshold_value is not None:
            alert.threshold_value = convert_numpy_types(threshold_value)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Alert updated",
            "alert": {
                "id": alert.id,
                "stock_symbol": alert.stock.symbol,
                "alert_type": alert.alert_type,
                "threshold_value": alert.threshold_value,
                "is_active": alert.is_active
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating alert: {str(e)}")
        return {"success": False, "message": f"Failed to update alert: {str(e)}"}

def delete_alert(alert_id: int) -> bool:
    """Delete an alert by ID"""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return {"success": False, "message": f"Alert with ID {alert_id} not found"}
        
        db.delete(alert)
        db.commit()
        
        return {"success": True, "message": f"Alert deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting alert: {str(e)}")
        return {"success": False, "message": f"Failed to delete alert: {str(e)}"} 