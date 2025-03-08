from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from services.alpaca_service import AlpacaService
from services.trading_strategy_service import TradingStrategyService

router = APIRouter(prefix="/api/trading", tags=["trading"])

# Initialize services
alpaca_service = AlpacaService()
strategy_service = TradingStrategyService()


# Models
class OrderRequest(BaseModel):
    symbol: str
    qty: float
    side: str
    type: str = "market"
    time_in_force: str = "day"
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None


class StrategyRequest(BaseModel):
    strategy_type: str
    params: Dict[str, Any]


# Routes
@router.get("/account")
async def get_account_info():
    """Get Alpaca account information"""
    try:
        return alpaca_service.get_account_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions():
    """Get current positions"""
    try:
        return alpaca_service.get_positions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders(status: Optional[str] = None):
    """Get orders with optional status filter"""
    try:
        return alpaca_service.get_orders(status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders")
async def place_order(order: OrderRequest):
    """Place an order"""
    try:
        if order.type == "market":
            return alpaca_service.place_market_order(order.symbol, order.qty, order.side, order.time_in_force)
        elif order.type == "limit" and order.limit_price:
            return alpaca_service.place_limit_order(
                order.symbol, order.qty, order.side, order.limit_price, order.time_in_force
            )
        elif order.type == "stop" and order.stop_price:
            return alpaca_service.place_stop_order(
                order.symbol, order.qty, order.side, order.stop_price, order.time_in_force
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid order parameters")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/orders/{order_id}")
async def cancel_order(order_id: str):
    """Cancel an order by ID"""
    try:
        return alpaca_service.cancel_order(order_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/orders")
async def cancel_all_orders():
    """Cancel all open orders"""
    try:
        return alpaca_service.cancel_all_orders()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-strategy")
async def execute_strategy(strategy_req: StrategyRequest, background_tasks: BackgroundTasks):
    """Execute a trading strategy"""
    try:
        strategy_type = strategy_req.strategy_type
        params = strategy_req.params

        if strategy_type == "prev_day_high":
            # Run in background to avoid blocking
            background_tasks.add_task(strategy_service.execute_prev_day_high_strategy, params)
            return {"success": True, "message": "Strategy execution started in background"}

        elif strategy_type == "consecutive_positive_candles":
            background_tasks.add_task(strategy_service.execute_consecutive_positive_candles_strategy, params)
            return {"success": True, "message": "Strategy execution started in background"}

        elif strategy_type == "open_below_prev_high":
            background_tasks.add_task(strategy_service.execute_open_below_prev_high_strategy, params)
            return {"success": True, "message": "Strategy execution started in background"}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy type: {strategy_type}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    timeframe: str = "1d",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None,
):
    """Get historical price data for a symbol"""
    try:
        return alpaca_service.get_historical_bars(symbol, timeframe, start_date, end_date, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
