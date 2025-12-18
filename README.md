# Inventory Reservation System

This Django project implements an inventory reservation system as per the requirements in `Final Take-Home Task`. 

## Design Decisions

### User System
No user authentication or session management was implemented because the requirements in `Final Take-Home Task` did not mention any authentication or session-related features. The system focuses solely on inventory management, reservations, and orders without user login.

### Database
SQLite was chosen as the database for simplicity and ease of setup, as no specific database requirements were mentioned in `Final Take-Home Task`.

### Background Tasks
Celery was integrated for periodic cleanup of expired reservations using Celery Beat, providing a robust way to handle background jobs as per Task 1 requirements.

### Containerization
Docker and Docker Compose are provided for easy deployment and environment consistency.

## Features

### Task 1: Inventory Reservation System
- Product inventory with `total_stock`, `available_stock`, and `reserved_stock`
- Invariant: `available_stock + reserved_stock = total_stock`
- Reservations created via `POST /api/reservations/` with 10-minute expiration
- Concurrency-safe using `select_for_update` and `transaction.atomic`
- Expired reservations cleaned up via Celery Beat every 5 minutes
- Management command `cleanup_reservations` available as alternative

### Task 2: Order State Machine
- State machine with allowed transitions:
  - pending → confirmed → processing → shipped → delivered
  - pending/confirmed → cancelled
  - shipped/delivered are immutable (no further transitions)
- Validation prevents invalid transitions
- Transition map implemented as dictionary in code

### Task 3: Concurrency Chaos Test
- Script `scripts/chaos_test.py` tests concurrency with 50 parallel reservation attempts on a product with 5 stock
- Exactly 5 reservations succeed, demonstrating proper concurrency handling
- Output shows succeeded/failed counts and final stock numbers

### Task 4: Performance Optimization
- `GET /api/orders/` supports filtering by date range, status, min/max total
- Sorting by newest (created_at) and highest value (total)
- Cursor pagination for large datasets
- Indexes added:
  - `Order(created_at)` for date range filtering
  - `Order(status)` for status filtering
  - `Order(total)` for min/max total filtering
  - Composite `Order(created_at, total)` for sorting
- Query optimization using `select_related` for user and `prefetch_related` for order items
- Query count: 2-3 queries per paginated request

### Task 5: Audit Log
- Records actor, action, object_type, object_id, old_value/new_value (JSON), timestamp
- Called explicitly from service layer
- Logs: reservation created/expired, order status changes, stock adjustments

### Task 6: Design Questions

#### Crash Recovery After Reservation
In case of server crash, expired reservations can be cleaned up using the management command or Celery Beat. For immediate recovery, implement a background job to periodically clean up expired reservations every minute.

#### Cleanup Strategy + Frequency
Use Celery Beat to run cleanup every 5 minutes. For cron: `*/5 * * * * python manage.py cleanup_reservations`

#### Multi-Warehouse Design
Use a Warehouse model with many-to-many relationship to products. Stock levels per warehouse. Reservation locks specific warehouse stock.

#### Caching Strategy
Cache product stock levels in Redis with 5-minute TTL. Invalidate on stock changes. Use cache-aside pattern.

#### Flow Diagram
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

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
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

4. For background tasks (optional):
   ```bash
   celery -A core.core worker --loglevel=info
   celery -A core.core beat --loglevel=info
   ```

## Docker Setup

```bash
docker-compose up --build
```

## API Endpoints

- `POST /api/reservations/` - Create a reservation
- `GET /api/products/` - List products
- `GET /api/orders/` - List orders with filters and sorting
- `POST /api/orders/{id}/confirm/` - Confirm an order
- `POST /api/orders/{id}/cancel/` - Cancel an order

Every API response includes a `request_id` (UUID) for tracing.

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

## Database Indexes

- `Order(created_at)`
- `Order(status)`
- `Order(total)`
- `Order(created_at, total)`