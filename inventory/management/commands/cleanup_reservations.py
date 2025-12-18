from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from inventory.models import Reservation, Product
from inventory.services import audit_log
import json

# was not used, just for display
class Command(BaseCommand):
    help = 'Clean up expired reservations and release stock'

    def handle(self, *args, **options):
        expired_reservations = Reservation.objects.filter(expires_at__lt=timezone.now())
        for reservation in expired_reservations:
            with transaction.atomic():
                product = Product.objects.select_for_update().get(pk=reservation.product.pk)
                product.available_stock += reservation.quantity
                product.reserved_stock -= reservation.quantity
                product.save()
                audit_log(
                    action='reservation_expired',
                    object_type='Reservation',
                    object_id=str(reservation.pk),
                    old_value={'product': str(product.pk), 'quantity': reservation.quantity},
                    new_value=None,
                    actor=None,
                )
                reservation.delete()
        self.stdout.write(f'Cleaned up {expired_reservations.count()} expired reservations')