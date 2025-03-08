import logging
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel

from backend.api.auth_routes import get_current_user
from backend.models.database import Alert, User
from backend.services.alert_service import (
    PERCENT_CHANGE,
    PRICE_ABOVE,
    PRICE_BELOW,
    VOLUME_ABOVE,
    alert_manager,
    create_alert,
    delete_alert,
    get_alerts_for_user,
    update_alert,
)

router = APIRouter()
logger = logging.getLogger(__name__)


class AlertCreate(BaseModel):
    stock_symbol: str
    alert_type: str
    threshold_value: float


class AlertResponse(BaseModel):
    id: int
    stock_symbol: str
    stock_name: str
    alert_type: str
    threshold_value: float
    is_active: bool
    created_at: str


@router.post("/create", response_model=AlertResponse)
async def add_alert(alert_data: AlertCreate, current_user: User = Depends(get_current_user)):
    """Create a new stock alert."""
    # Validate alert type
    valid_alert_types = [PRICE_ABOVE, PRICE_BELOW, VOLUME_ABOVE, PERCENT_CHANGE]
    if alert_data.alert_type not in valid_alert_types:
        raise HTTPException(status_code=400, detail=f"Invalid alert type. Must be one of {valid_alert_types}")

    result = create_alert(
        alert_data.stock_symbol,
        current_user,  # Pass user object instead of email
        alert_data.alert_type,
        alert_data.threshold_value,
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to create alert")

    return result


@router.get("/user/alerts", response_model=List[AlertResponse])
async def get_user_alerts(current_user: User = Depends(get_current_user)):
    """Get all alerts for the current user."""
    alerts = get_alerts_for_user(current_user)  # Pass user object instead of email
    return alerts


@router.put("/{alert_id}")
async def update_alert_status(
    alert_id: int, is_active: bool = Body(...), current_user: User = Depends(get_current_user)
):
    """Update an alert's active status."""
    try:
        alert = Alert.get((Alert.id == alert_id) & (Alert.user == current_user))
    except Alert.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    result = update_alert(alert_id, is_active=is_active)
    if not result:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update alert")
    return result


@router.delete("/{alert_id}")
async def remove_alert(alert_id: int, current_user: User = Depends(get_current_user)):
    """Delete an alert."""
    try:
        alert = Alert.get((Alert.id == alert_id) & (Alert.user == current_user))
    except Alert.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    if delete_alert(alert_id):
        return {"message": "Alert deleted successfully"}
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete alert")


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
            {"type": PRICE_ABOVE, "description": "Alert when price goes above threshold"},
            {"type": PRICE_BELOW, "description": "Alert when price goes below threshold"},
            {"type": VOLUME_ABOVE, "description": "Alert when volume goes above threshold"},
            {"type": PERCENT_CHANGE, "description": "Alert when percent change exceeds threshold"},
        ]
    }
