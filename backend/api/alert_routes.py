from fastapi import APIRouter, HTTPException, Depends, Query, Body
from backend.services.alert_service import (
    create_alert, 
    get_alerts_for_user, 
    update_alert, 
    delete_alert,
    alert_manager,
    PRICE_ABOVE, 
    PRICE_BELOW, 
    VOLUME_ABOVE, 
    PERCENT_CHANGE
)
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import logging
import rookiepy


router = APIRouter()
logger = logging.getLogger(__name__)

class AlertCreate(BaseModel):
    stock_symbol: str
    user_email: EmailStr
    alert_type: str
    threshold_value: float

class AlertUpdate(BaseModel):
    is_active: Optional[bool] = None
    threshold_value: Optional[float] = None

@router.post("/create")
async def add_alert(alert_data: AlertCreate):
    """Create a new stock alert."""
    # Validate alert type
    valid_alert_types = [PRICE_ABOVE, PRICE_BELOW, VOLUME_ABOVE, PERCENT_CHANGE]
    if alert_data.alert_type not in valid_alert_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid alert type. Must be one of {valid_alert_types}"
        )
        
    result = create_alert(
        alert_data.stock_symbol,
        alert_data.user_email,
        alert_data.alert_type,
        alert_data.threshold_value
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create alert")
        
    return result

@router.get("/user/{email}")
async def get_user_alerts(email: EmailStr):
    """Get all alerts for a specific user."""
    alerts = get_alerts_for_user(email)
    return {"alerts": alerts}

@router.put("/{alert_id}")
async def modify_alert(alert_id: int, alert_data: AlertUpdate):
    """Update an existing alert."""
    result = update_alert(
        alert_id,
        alert_data.is_active,
        alert_data.threshold_value
    )
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
    return result

@router.delete("/{alert_id}")
async def remove_alert(alert_id: int):
    """Delete an alert."""
    success = delete_alert(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
    return {"message": f"Alert {alert_id} deleted successfully"}

@router.get("/triggered")
async def get_triggered_alerts(limit: int = Query(50, ge=1, le=100)):
    """Get recently triggered alerts."""
    alerts = alert_manager.get_recent_triggered_alerts(limit)
    return {"triggered_alerts": alerts}

@router.get("/types")
async def get_alert_types():
    """Get available alert types."""
    return {
        "alert_types": [
            {
                "type": PRICE_ABOVE,
                "description": "Alert when price goes above threshold"
            },
            {
                "type": PRICE_BELOW,
                "description": "Alert when price goes below threshold"
            },
            {
                "type": VOLUME_ABOVE,
                "description": "Alert when volume goes above threshold"
            },
            {
                "type": PERCENT_CHANGE,
                "description": "Alert when percent change exceeds threshold"
            }
        ]
    } 