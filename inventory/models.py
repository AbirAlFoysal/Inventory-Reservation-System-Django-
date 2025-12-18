from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.core.abstract_model import BaseModel


class Product(BaseModel):
    name = models.CharField(max_length=255)
    total_stock = models.PositiveIntegerField()
    available_stock = models.PositiveIntegerField()
    reserved_stock = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    # since i am using sqlite, otherwise i would have used CheckConstraint
    def save(self, *args, **kwargs):
        if self.available_stock + self.reserved_stock != self.total_stock:
            raise ValueError("available_stock + reserved_stock must equal to total_stock")
        super().save(*args, **kwargs)


class Reservation(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.product.name} - {self.expires_at}"

    def is_expired(self):
        return timezone.now() > self.expires_at



class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    PROCESSING = 'processing', 'Processing'
    SHIPPED = 'shipped', 'Shipped'
    DELIVERED = 'delivered', 'Delivered'
    CANCELLED = 'cancelled', 'Cancelled'

TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}

class Order(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING, db_index=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_at', 'total']),
        ]
        ordering = ['-created_at']

    def can_transition_to(self, new_status):
        return new_status in TRANSITIONS[self.status]



class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

class AuditLog(BaseModel):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    object_type = models.CharField(max_length=255)
    object_id = models.CharField(max_length=255)
    old_value = models.JSONField(null=True)
    new_value = models.JSONField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
