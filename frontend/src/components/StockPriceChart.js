import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  ReferenceLine
} from 'recharts';
import {
  Box,
  Card,
  CardContent,
  Typography,
  ButtonGroup,
  Button,
  useTheme,
  Skeleton
} from '@mui/material';

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }) => {
  const theme = useTheme();

  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const isPositive = data.close >= data.open;

    return (
      <Card sx={{
        bgcolor: 'background.paper',
        p: 1,
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        border: '1px solid rgba(255, 255, 255, 0.05)',
      }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
          {new Date(label).toLocaleDateString()}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Open: <span style={{ color: theme.palette.primary.main }}>${data.open.toFixed(2)}</span>
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Close: <span style={{ color: isPositive ? theme.palette.success.main : theme.palette.error.main }}>
            ${data.close.toFixed(2)}
          </span>
        </Typography>
        <Typography variant="body2" color="text.secondary">
          High: <span style={{ color: theme.palette.success.main }}>${data.high.toFixed(2)}</span>
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Low: <span style={{ color: theme.palette.error.main }}>${data.low.toFixed(2)}</span>
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Volume: {Intl.NumberFormat().format(data.volume)}
        </Typography>
      </Card>
    );
  }

  return null;
};

const StockPriceChart = ({ data, title, isLoading }) => {
  const theme = useTheme();
  const [timeRange, setTimeRange] = useState('1M');

  // Filter data based on selected time range
  const getFilteredData = () => {
    if (!data || data.length === 0) return [];

    const now = new Date();
    let startDate = new Date();

    switch (timeRange) {
      case '1W':
        startDate.setDate(now.getDate() - 7);
        break;
      case '1M':
        startDate.setMonth(now.getMonth() - 1);
        break;
      case '3M':
        startDate.setMonth(now.getMonth() - 3);
        break;
      case '6M':
        startDate.setMonth(now.getMonth() - 6);
        break;
      case '1Y':
        startDate.setFullYear(now.getFullYear() - 1);
        break;
      case 'ALL':
      default:
        return data;
    }

    return data.filter(item => new Date(item.date) >= startDate);
  };

  const filteredData = getFilteredData();

  // Calculate if overall trend is positive
  const isPositiveTrend = filteredData.length > 1 &&
    filteredData[filteredData.length - 1].close > filteredData[0].close;

  // Calculate min and max for Y axis
  const minValue = filteredData.length > 0
    ? Math.min(...filteredData.map(item => item.low)) * 0.98
    : 0;

  const maxValue = filteredData.length > 0
    ? Math.max(...filteredData.map(item => item.high)) * 1.02
    : 100;

  // Gradient colors
  const gradientColors = isPositiveTrend
    ? ['rgba(50, 215, 148, 0)', 'rgba(50, 215, 148, 0.4)']
    : ['rgba(255, 71, 87, 0)', 'rgba(255, 71, 87, 0.4)'];

  const lineColor = isPositiveTrend ? '#32d794' : '#ff4757';

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" component="div">
            {title}
          </Typography>
          <ButtonGroup size="small" variant="outlined" aria-label="time range">
            {['1W', '1M', '3M', '6M', '1Y', 'ALL'].map(range => (
              <Button
                key={range}
                onClick={() => setTimeRange(range)}
                variant={timeRange === range ? 'contained' : 'outlined'}
              >
                {range}
              </Button>
            ))}
          </ButtonGroup>
        </Box>

        <Box sx={{ height: 300, width: '100%' }}>
          {isLoading ? (
            <Skeleton variant="rectangular" height={300} animation="wave" />
          ) : filteredData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={filteredData}
                margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
              >
                <defs>
                  <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={gradientColors[1]} stopOpacity={0.8} />
                    <stop offset="95%" stopColor={gradientColors[0]} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: theme.palette.text.secondary }}
                  tickFormatter={(tick) => {
                    const date = new Date(tick);
                    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                  }}
                />
                <YAxis
                  domain={[minValue, maxValue]}
                  tick={{ fill: theme.palette.text.secondary }}
                  tickFormatter={(tick) => `$${tick.toFixed(2)}`}
                />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine
                  y={filteredData[0]?.close}
                  stroke="rgba(255,255,255,0.3)"
                  strokeDasharray="3 3"
                />
                <Area
                  type="monotone"
                  dataKey="close"
                  stroke={lineColor}
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <Box sx={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Typography variant="body1" color="text.secondary">
                No data available
              </Typography>
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default StockPriceChart;
