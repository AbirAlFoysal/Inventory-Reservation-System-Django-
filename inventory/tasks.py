from celery import shared_task
from django.db import transaction
from django.utils import timezone
from inventory.models import Reservation
from inventory.services import audit_log


@shared_task
def cleanup_expired_reservations():
    expired_reservations = Reservation.objects.filter(
        expires_at__lt=timezone.now(),
        order__isnull=True   
    ).select_related('product')

    cleaned_count = 0
    for reservation in expired_reservations:
        product = reservation.product
        with transaction.atomic():
            product.available_stock += reservation.quantity
            product.reserved_stock -= reservation.quantity
            product.save()

            audit_log(
                action='reservation_expired',
                object_type='Reservation',
                object_id=str(reservation.pk),
                old_value={'quantity': reservation.quantity, 'product': str(product.pk)},
                new_value=None,
                actor=None
            )
            reservation.delete()
            cleaned_count += 1

    return cleaned_count