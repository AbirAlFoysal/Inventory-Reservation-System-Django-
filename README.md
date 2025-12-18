# Inventory Reservation System

This Django project implements an inventory reservation system with order state machine, concurrency handling, and audit logging.

## Features

- Product inventory management with available and reserved stock
- Reservation system with 10-minute expiration
- Order state machine with validation
- Audit logging for key actions
- REST API with request_id tracing
- Concurrency-safe operations using database locks

## Setup

1. Install dependencies:
   ```bash
   pip install django djangorestframework
   ```

2. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. Run the server:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

- `POST /api/reservations/` - Create a reservation
- `GET /api/orders/` - List orders with filters and sorting
- `POST /api/orders/{id}/confirm/` - Confirm an order
- `POST /api/orders/{id}/cancel/` - Cancel an order

## Management Commands

- `python manage.py cleanup_reservations` - Clean up expired reservations

## Tests

Run tests:
```bash
python manage.py test
```

## Concurrency Test

Run the chaos test script:
```bash
python scripts/chaos_test.py
```

## Performance Optimization

### Indexes Added

- Index on `Order.created_at` for date range filtering
- Index on `Order.status` for status filtering
- Index on `Order.total` for min/max total filtering
- Composite index on `(created_at, total)` for sorting by newest and highest value

### Query Optimization

- Used `select_related` for user in Order queries
- Used `prefetch_related` for order items and products
- Cursor pagination for large result sets

### Query Count

The `/api/orders/` endpoint uses optimized queries with select_related and prefetch_related to minimize database hits. Typical query count for a paginated list is 2-3 queries (main query + prefetch).

## Audit Log

Audit log records:
- Reservation creation
- Reservation expiration
- Order status changes
- Stock adjustments

## Design Questions

### Crash Recovery After Reservation
In case of server crash, expired reservations can be cleaned up using the management command. For immediate recovery, implement a background job (Celery beat) to periodically clean up expired reservations every minute.

### Cleanup Strategy + Frequency
Use Celery beat to run cleanup every 5 minutes. For cron: `*/5 * * * * python manage.py cleanup_reservations`

### Multi-Warehouse Design
Use a Warehouse model with many-to-many relationship to products. Stock levels per warehouse. Reservation locks specific warehouse stock.

### Caching Strategy
Cache product stock levels in Redis with 5-minute TTL. Invalidate on stock changes. Use cache-aside pattern.

### Flow Diagram

```
User Request Reservation
    ↓
Validate Stock Availability
    ↓
Lock Product Row (select_for_update)
    ↓
Deduct from Available, Add to Reserved
    ↓
Create Reservation (10 min expiry)
    ↓
Audit Log: Reservation Created
    ↓
Return Success with request_id
```

## Database Indexes

- `Order(created_at)`
- `Order(status)`
- `Order(total)`
- `Order(created_at, total)`