import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.core.settings')
django.setup()

from inventory.models import Product, Reservation, Order, AuditLog
from django.contrib.auth.models import User


def populate_database():
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@gmail.com'}
    )

    products_data = [
        {'name': 'Laptop', 'total_stock': 100, 'available_stock': 80, 'reserved_stock': 20},
        {'name': 'Mouse', 'total_stock': 200, 'available_stock': 150, 'reserved_stock': 50},
        {'name': 'Keyboard', 'total_stock': 150, 'available_stock': 120, 'reserved_stock': 30},
        {'name': 'Monitor', 'total_stock': 50, 'available_stock': 40, 'reserved_stock': 10},
    ]

    products = []
    for data in products_data:
        product, created = Product.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        products.append(product)

    for product in products:
        if product.available_stock > 10:
            Reservation.objects.get_or_create(
                product=product,
                quantity=5,
                expires_at=timezone.now() + timedelta(hours=1),
                defaults={}
            )

    for i in range(3):
        order = Order.objects.create(
            user=user,
            status='pending'
        )
        
    AuditLog.objects.get_or_create(
        actor=user,
        action='database_populated',
        object_type='System',
        object_id='1',
        old_value={},
        new_value={'message': 'Sample data created'},
    )

    print("Database populated with sample data!")