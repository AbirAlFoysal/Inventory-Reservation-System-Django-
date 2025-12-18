from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import Product, Reservation, Order, AuditLog
from .serializers import ProductSerializer, ReservationSerializer, OrderSerializer
from .services import transition_order
from core.core.paginator import GlobalPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
import json


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = GlobalPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        'name': ['exact'],
        'total_stock': ['exact'],
        'available_stock': ['exact'],
        'reserved_stock': ['exact'],
        'created_at': ['gte', 'lte'],
    }
    ordering_fields = [
        'name',
        'total_stock',
        'available_stock',
        'reserved_stock',
        'created_at',
    ]
    ordering = ['-created_at']

from django.db.models import F

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    http_method_names = ["post"]

    def create(self, request, *args, **kwargs):
        product_id = request.data.get('product')
        try:
            quantity = int(request.data.get('quantity'))
            if quantity <= 0:
                return Response({'error': 'Quantity must be greater than zero'}, status=400)
        except (TypeError, ValueError):
            return Response({'error': 'Invalid quantity'}, status=400)

        try:
            with transaction.atomic():
                # Attempt to decrement stock atomically
                updated = Product.objects.filter(
                    pk=product_id,
                    available_stock__gte=quantity
                ).update(
                    available_stock=F('available_stock') - quantity,
                    reserved_stock=F('reserved_stock') + quantity
                )

                if not updated:
                    return Response({'error': 'Not enough stock or product not found'}, status=400)

                # Fetch the product again for reference
                product = Product.objects.get(pk=product_id)

                expires_at = timezone.now() + timedelta(minutes=10)
                reservation = Reservation.objects.create(
                    product=product,
                    quantity=quantity,
                    expires_at=expires_at
                )

                AuditLog.objects.create(
                    actor=request.user if request.user.is_authenticated else None,
                    action='reservation_created',
                    object_type='Reservation',
                    object_id=str(reservation.pk),
                    new_value={
                        'product': str(product.pk),
                        'quantity': quantity
                    },
                )

        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)
        except Exception as e:
            return Response({'error': 'Something went wrong'}, status=500)

        serializer = self.get_serializer(reservation)
        return Response(serializer.data, status=201)



class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    pagination_class = GlobalPagination
    queryset = Order.objects.select_related('user').prefetch_related('items__product')
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        'status': ['exact'],
        'created_at': ['gte', 'lte'],
        'total': ['gte', 'lte'],
    }
    ordering_fields = ['created_at', 'total']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        try:
            transition_order(order=order, new_status='confirmed', actor=request.user if request.user.is_authenticated else None)
            return Response({'status': 'confirmed'})
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            transition_order(order=order, new_status='cancelled', actor=request.user if request.user.is_authenticated else None)
            return Response({'status': 'cancelled'})
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
