import React, { useState, useEffect, useRef } from 'react';
import { NotificationContainer, NotificationManager } from 'react-notifications';
import 'react-notifications/lib/notifications.css';
import { API_URL } from '../config';
import './NotificationCenter.css'; // We'll create this for custom styling

const NotificationCenter = () => {
    const [socket, setSocket] = useState(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 5;
    const reconnectTimeoutRef = useRef(null);

    // Connect to WebSocket on component mount
    useEffect(() => {
        // Clear any existing reconnect timeout
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
        }

        // Create WebSocket connection
        const wsUrl = API_URL.replace('http://', 'ws://').replace('https://', 'wss://');
        const ws = new WebSocket(`${wsUrl}/ws`);

        ws.onopen = () => {
            // Reset reconnect attempts on successful connection
            reconnectAttempts.current = 0;
            console.log('WebSocket connection established successfully');
        };

        ws.onmessage = (event) => {
            try {
                console.log('WebSocket message received:', event.data);
                const data = JSON.parse(event.data);

                if (data.type === 'new_crossing_stocks' && data.data && data.data.length > 0) {
                    // Process each stock for notification
                    data.data.forEach(stock => {
                        const title = `${stock.symbol} Crossed Above Previous Day High!`;
                        const message = (
                            <div className="stock-notification">
                                <div className="notification-title">{stock.name}</div>
                                <div className="notification-price">
                                    <span className="label">Current Price:</span> ${stock.current_price}
                                </div>
                                <div className="notification-details">
                                    <div><span className="label">Change:</span> {stock.percent_change}%</div>
                                    <div><span className="label">Above Prev High:</span> {stock.percent_above_prev_high}%</div>
                                </div>
                            </div>
                        );

                        // Create notification
                        NotificationManager.success(
                            message,
                            title,
                            10000, // 10 seconds
                            () => {}
                        );

                        // Play notification sound if available
                        playNotificationSound();
                    });
                }
                else if (data.type === 'crossed_above_prev_day_high' && data.data && data.data.length > 0) {
                    // Process each stock for notification
                    data.data.forEach(stock => {
                        const title = `${stock.symbol} - Breakout Alert!`;
                        const message = (
                            <div className="stock-notification">
                                <div className="notification-title">{stock.name}</div>
                                <div className="notification-description">
                                    just crossed above previous day high of ${stock.previous_day_high}
                                </div>
                                <div className="notification-price">
                                    <span className="label">Current Price:</span> ${stock.current_price}
                                </div>
                                <div className="notification-details">
                                    <div><span className="label">Change:</span> {stock.percent_change}%</div>
                                    {stock.percent_above_prev_high && (
                                        <div><span className="label">Above Prev High:</span> {stock.percent_above_prev_high}%</div>
                                    )}
                                </div>
                            </div>
                        );

                        // Create notification with a warning style
                        NotificationManager.warning(
                            message,
                            title,
                            10000, // 10 seconds
                            () => {}
                        );

                        // Play notification sound if available
                        playNotificationSound();
                    });
                }
            } catch (error) {
                console.error('Error processing WebSocket message:', error);
            }
        };

        ws.onclose = (event) => {
            // Only attempt to reconnect if we haven't exceeded max attempts
            if (reconnectAttempts.current < maxReconnectAttempts) {
                reconnectAttempts.current += 1;

                // Exponential backoff: wait longer between each attempt
                const delay = Math.min(30000, 1000 * Math.pow(2, reconnectAttempts.current));

                // Set timeout for reconnection
                reconnectTimeoutRef.current = setTimeout(() => {
                    setSocket(null); // This will trigger useEffect to reconnect
                }, delay);
            }
        };

        setSocket(ws);

        // Cleanup on unmount
        return () => {
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
            if (ws) {
                ws.close();
            }
        };
    }, [socket === null]);

    // Keep WebSocket alive
    useEffect(() => {
        if (!socket) return;

        const interval = setInterval(() => {
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send('ping');
            }
        }, 30000); // Send ping every 30 seconds

        return () => clearInterval(interval);
    }, [socket]);

    // Function to play notification sound
    const playNotificationSound = () => {
        try {
            const audio = new Audio('/notification-sound.mp3');
            audio.play();
        } catch (e) {
            console.log('Notification sound not available:', e);
        }
    };

    return <NotificationContainer />;
};

export default NotificationCenter;
