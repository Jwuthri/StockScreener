import React from 'react';
import { Card, Badge, Row, Col, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { BsArrowUpCircleFill } from 'react-icons/bs';

const StockCrossingAlert = ({ stock }) => {
  const {
    symbol,
    name,
    percent_change,
    current_price,
    previous_day_high,
    percent_above_prev_high
  } = stock;

  // Calculate color based on percent change
  const getChangeColor = (percent) => {
    if (percent >= 10) return 'success';
    if (percent >= 5) return 'info';
    if (percent >= 2) return 'primary';
    if (percent >= 0) return 'secondary';
    return 'danger';
  };

  return (
    <Card className="mb-3 border-success stock-alert-card">
      <Card.Header className="d-flex justify-content-between align-items-center bg-success text-white">
        <div>
          <BsArrowUpCircleFill className="me-2" />
          {symbol} Crossed Previous Day High
        </div>
        <Badge bg={getChangeColor(percent_change)} pill>
          {percent_change}%
        </Badge>
      </Card.Header>
      <Card.Body>
        <Card.Title>{name}</Card.Title>
        <Row className="my-3">
          <Col>
            <div className="text-muted mb-1">Current Price</div>
            <h5>${current_price}</h5>
          </Col>
          <Col>
            <div className="text-muted mb-1">Previous Day High</div>
            <h5>${previous_day_high}</h5>
          </Col>
          <Col>
            <div className="text-muted mb-1">Above PDH</div>
            <h5 className="text-success">+{percent_above_prev_high}%</h5>
          </Col>
        </Row>
        <div className="d-grid gap-2 d-md-flex justify-content-md-end">
          <Link to={`/stock/${symbol}`}>
            <Button variant="outline-primary" size="sm">View Details</Button>
          </Link>
        </div>
      </Card.Body>
    </Card>
  );
};

export default StockCrossingAlert; 