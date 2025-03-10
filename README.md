# Stock Screener with Real-Time Breakout Notifications

A powerful stock screener application that offers various screening strategies, real-time data, and notifications for important market events.

## Features

- **Multiple Screening Strategies**:
  - Stocks with consecutive positive/negative candles
  - Stocks crossing above previous day high
  - Stocks crossing below previous day low
  - Stocks with open below previous day high
  - Custom filtering by price, volume, change percentage, sector, etc.

- **Real-Time Breakout Notifications**:
  - Get instant alerts when stocks cross above previous day high
  - Monitor stocks that opened below the previous day high and alert when they break out
  - Sound notifications for important breakouts

- **Advanced Technical Analysis**:
  - Price history charts with volume analysis
  - Support for multiple timeframes
  - Sector & industry analysis

## Setup and Installation

### Backend

```
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend

```
cd frontend
npm install
npm start
```

## Architecture

The application consists of a FastAPI backend with WebSocket support for real-time notifications and a React frontend for a responsive user interface.

### Key Components

1. **Open Below Prev High Screener**:
   - Identifies stocks that opened below the previous day's high
   - Provides a potential trading opportunity

2. **Real-Time Breakout Monitoring**:
   - Continuously monitors stocks that opened below previous day high
   - Sends real-time alerts when they cross above the previous day high
   - Notifies users through popup notifications with sound

## Usage

1. Navigate to the Stock Screener page
2. Select the "Open Below Prev High" screener
3. Set your filters (price, volume, etc.)
4. Run the screener
5. The system will automatically monitor these stocks for breakouts
6. Receive real-time notifications when stocks break out above previous day high

## Technologies Used

- **Backend**: Python, FastAPI, WebSockets, SQLAlchemy
- **Frontend**: React, Material-UI, Chart.js
- **Data**: TradingView API integration

## License

MIT
