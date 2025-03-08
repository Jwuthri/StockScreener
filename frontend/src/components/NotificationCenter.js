import React, { useState, useEffect, useRef } from 'react';
import { Toast, ToastContainer } from 'react-bootstrap';
import { API_URL } from '../config';

const NotificationCenter = () => {
    const [notifications, setNotifications] = useState([]);
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
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);

                if (data.type === 'new_crossing_stocks' && data.data && data.data.length > 0) {
                    // Create notifications for each new stock
                    const newNotifications = data.data.map(stock => ({
                        id: `${stock.symbol}-${Date.now()}`,
                        title: `${stock.symbol} Crossed Above Previous Day High!`,
                        body: `${stock.name} is now ${stock.percent_above_prev_high}% above its previous day high of $${stock.previous_day_high}`,
                        timestamp: new Date(),
                        stock: stock
                    }));

                    // Add new notifications to the list
                    setNotifications(prev => [...newNotifications, ...prev].slice(0, 10)); // Keep last 10 notifications
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

    // Remove a notification
    const removeNotification = (id) => {
        setNotifications(prev => prev.filter(notif => notif.id !== id));
    };

    return (
        <ToastContainer position="top-end" className="p-3" style={{ zIndex: 1060 }}>
            {notifications.map(notification => (
                <Toast
                    key={notification.id}
                    onClose={() => removeNotification(notification.id)}
                    show={true}
                    delay={10000}
                    autohide
                    bg="success"
                    className="mb-2"
                >
                    <Toast.Header>
                        <strong className="me-auto">{notification.title}</strong>
                        <small>{new Date(notification.timestamp).toLocaleTimeString()}</small>
                    </Toast.Header>
                    <Toast.Body className="text-white">
                        {notification.body}
                        {notification.stock && (
                            <>
                                <div className="mt-2">
                                    <strong>Current Price:</strong> ${notification.stock.current_price}
                                </div>
                                <div>
                                    <strong>Change:</strong> {notification.stock.percent_change}%
                                </div>
                            </>
                        )}
                    </Toast.Body>
                </Toast>
            ))}
        </ToastContainer>
    );
};

export default NotificationCenter;
