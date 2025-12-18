from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet,
    ReservationViewSet,
    OrderViewSet
)


router = DefaultRouter()

router.register(r'products', ProductViewSet, basename='products')
router.register(r'reservations', ReservationViewSet, basename='reservations')
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('', include(router.urls)),
]