from celery import shared_task
from django.db import transaction
from django.utils import timezone
from inventory.models import Reservation, AuditLog
from inventory.services import audit_log


@shared_task
def cleanup_expired_reservations():
    """
    Cleanup expired reservations: release stock and audit.
    """
    expired_reservations = Reservation.objects.filter(
        expires_at__lt=timezone.now(),
        order__isnull=True  # Only reservations not converted to orders
    ).select_related('product')

    cleaned_count = 0
    for reservation in expired_reservations:
        product = reservation.product
        with transaction.atomic():
            product.available_stock += reservation.quantity
            product.reserved_stock -= reservation.quantity
            product.save()

            audit_log(
                'reservation_expired',
                'Reservation',
                str(reservation.pk),
                {'quantity': reservation.quantity, 'product': str(product.pk)},
                None,
                None
            )
            reservation.delete()
            cleaned_count += 1

    return cleaned_count