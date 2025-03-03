import React, { useRef, useEffect } from 'react';
import { Box, Typography } from '@mui/material';

const StockChartFallback = ({ data = [], width = '100%', height = 400 }) => {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    if (!canvasRef.current || !data || data.length === 0) return;
    
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    // Set canvas dimensions with higher resolution for retina displays
    const dpr = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    context.scale(dpr, dpr);
    
    // Clear canvas
    context.clearRect(0, 0, canvas.width, canvas.height);
    
    // Calculate dimensions
    const canvasWidth = canvas.offsetWidth;
    const canvasHeight = canvas.offsetHeight;
    const paddingX = 50;
    const paddingY = 50;
    const chartWidth = canvasWidth - (paddingX * 2);
    const chartHeight = canvasHeight - (paddingY * 2);
    
    // Calculate value range
    const values = data.map(d => d.value);
    const maxValue = Math.max(...values);
    const minValue = Math.min(...values);
    const valueRange = maxValue - minValue || 1;
    
    // Draw background grid
    context.strokeStyle = '#2a2a3c';
    context.lineWidth = 0.5;
    
    // Vertical grid lines
    for (let i = 0; i <= 5; i++) {
      const x = paddingX + (chartWidth * i / 5);
      context.beginPath();
      context.moveTo(x, paddingY);
      context.lineTo(x, paddingY + chartHeight);
      context.stroke();
    }
    
    // Horizontal grid lines
    for (let i = 0; i <= 5; i++) {
      const y = paddingY + (chartHeight * i / 5);
      context.beginPath();
      context.moveTo(paddingX, y);
      context.lineTo(paddingX + chartWidth, y);
      context.stroke();
    }
    
    // Draw bars
    const barWidth = chartWidth / (data.length * 1.5);
    
    data.forEach((point, index) => {
      const normalizedValue = (point.value - minValue) / valueRange;
      const barHeight = normalizedValue * chartHeight;
      
      const x = paddingX + ((index / (data.length - 1)) * chartWidth) - (barWidth / 2);
      const y = paddingY + chartHeight - barHeight;
      
      // Draw 3D-like bar with shading
      const barColor = point.value >= 0 ? '#32d794' : '#ff4757';
      
      // Main bar face
      context.fillStyle = barColor;
      context.fillRect(x, y, barWidth, barHeight);
      
      // Darker side for 3D effect
      context.fillStyle = darkenColor(barColor, 30);
      context.beginPath();
      context.moveTo(x + barWidth, y);
      context.lineTo(x + barWidth + 10, y - 10);
      context.lineTo(x + barWidth + 10, y + barHeight - 10);
      context.lineTo(x + barWidth, y + barHeight);
      context.closePath();
      context.fill();
      
      // Lighter top for 3D effect (only for positive values)
      context.fillStyle = lightenColor(barColor, 20);
      context.beginPath();
      context.moveTo(x, y);
      context.lineTo(x + barWidth, y);
      context.lineTo(x + barWidth + 10, y - 10);
      context.lineTo(x + 10, y - 10);
      context.closePath();
      context.fill();
      
      // Highlight important points
      if (point.isHighlighted) {
        context.strokeStyle = '#ffffff';
        context.lineWidth = 2;
        context.strokeRect(x, y, barWidth, barHeight);
        
        // Add value label
        context.fillStyle = '#ffffff';
        context.font = 'bold 12px Arial';
        context.textAlign = 'center';
        context.fillText(
          point.value.toFixed(2), 
          x + barWidth / 2, 
          y - 15
        );
      }
    });
    
    // Draw connecting line
    context.beginPath();
    context.strokeStyle = '#6562fc';
    context.lineWidth = 2;
    
    data.forEach((point, index) => {
      const normalizedValue = (point.value - minValue) / valueRange;
      const x = paddingX + ((index / (data.length - 1)) * chartWidth);
      const y = paddingY + chartHeight - (normalizedValue * chartHeight);
      
      if (index === 0) {
        context.moveTo(x, y);
      } else {
        context.lineTo(x, y);
      }
    });
    
    context.stroke();
    
  }, [data]);
  
  // Helper functions for color manipulation
  const darkenColor = (color, percent) => {
    const num = parseInt(color.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) - amt;
    const G = (num >> 8 & 0x00FF) - amt;
    const B = (num & 0x0000FF) - amt;
    
    return '#' + (
      0x1000000 + 
      (R < 0 ? 0 : R) * 0x10000 + 
      (G < 0 ? 0 : G) * 0x100 + 
      (B < 0 ? 0 : B)
    ).toString(16).slice(1);
  };
  
  const lightenColor = (color, percent) => {
    const num = parseInt(color.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = Math.min(255, (num >> 16) + amt);
    const G = Math.min(255, (num >> 8 & 0x00FF) + amt);
    const B = Math.min(255, (num & 0x0000FF) + amt);
    
    return '#' + (
      0x1000000 + 
      R * 0x10000 + 
      G * 0x100 + 
      B
    ).toString(16).slice(1);
  };
  
  return (
    <Box sx={{ width, height, position: 'relative' }}>
      <canvas 
        ref={canvasRef}
        style={{ 
          width: '100%', 
          height: '100%',
          display: 'block'
        }}
      />
      {(!data || data.length === 0) && (
        <Typography 
          variant="body1" 
          sx={{ 
            position: 'absolute', 
            top: '50%', 
            left: '50%', 
            transform: 'translate(-50%, -50%)',
            color: 'text.secondary'
          }}
        >
          No data available
        </Typography>
      )}
    </Box>
  );
};

export default StockChartFallback; 