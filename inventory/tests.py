from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.exceptions import ValidationError
from .models import Product, Reservation, Order
from inventory.services import transition_order
from django.core.management import call_command


class ProductModelTest(TestCase):
    def test_invariant(self):
        product = Product(name='Test', total_stock=10, available_stock=7, reserved_stock=3)
        product.save() 
        product.available_stock = 6
        with self.assertRaises(ValueError):
            product.save()

class ReservationModelTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Test', total_stock=10, available_stock=10, reserved_stock=0)

    def test_create_reservation(self):
        reservation = Reservation.objects.create(
            product=self.product,
            quantity=2,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        self.assertEqual(reservation.quantity, 2)
        # Stock update is done in view, not model

    def test_expired_reservation(self):
        past = timezone.now() - timedelta(minutes=1)
        reservation = Reservation.objects.create(
            product=self.product,
            quantity=2,
            expires_at=past
        )
        self.assertTrue(reservation.is_expired())

class OrderStateMachineTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'pass')
        self.order = Order.objects.create(user=self.user)

    def test_valid_transitions(self):
        
        transition_order(order=self.order, new_status='confirmed', actor=self.user)
        self.assertEqual(self.order.status, 'confirmed')

        transition_order(order=self.order, new_status='processing', actor=self.user)
        self.assertEqual(self.order.status, 'processing')

        transition_order(order=self.order, new_status='shipped', actor=self.user)
        self.assertEqual(self.order.status, 'shipped')

        transition_order(order=self.order, new_status='delivered', actor=self.user)
        self.assertEqual(self.order.status, 'delivered')

    def test_invalid_transitions(self):
        with self.assertRaises(ValidationError):
            transition_order(order=self.order, new_status='shipped', actor=self.user)

        transition_order(order=self.order, new_status='confirmed', actor=self.user)
        with self.assertRaises(ValidationError):
            transition_order(order=self.order, new_status='delivered', actor=self.user)

        transition_order(order=self.order, new_status='processing', actor=self.user)
        transition_order(order=self.order, new_status='shipped', actor=self.user)
        with self.assertRaises(ValidationError):
            transition_order(order=self.order, new_status='cancelled', actor=self.user)

    def test_cancel_transitions(self):
        transition_order(order=self.order, new_status='cancelled', actor=self.user)
        self.assertEqual(self.order.status, 'cancelled')

        order2 = Order.objects.create(user=self.user, status='confirmed')
        transition_order(order=order2, new_status='cancelled', actor=self.user)
        self.assertEqual(order2.status, 'cancelled')

class ReservationAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'pass')
        self.product = Product.objects.create(name='Test', total_stock=10, available_stock=10, reserved_stock=0)
        self.client.force_authenticate(user=self.user)

    def test_create_reservation_success(self):
        response = self.client.post('/api/reservations/', {'product': str(self.product.pk), 'quantity': 3})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_stock, 7)
        self.assertEqual(self.product.reserved_stock, 3)
        self.assertIn('request_id', response.data)

    def test_create_reservation_insufficient_stock(self):
        response = self.client.post('/api/reservations/', {'product': str(self.product.pk), 'quantity': 15})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class OrderAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'pass')
        self.client.force_authenticate(user=self.user)
        self.order = Order.objects.create(user=self.user)

    def test_confirm_order(self):
        response = self.client.post(f'/api/orders/{self.order.pk}/confirm/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')

    def test_cancel_order(self):
        response = self.client.post(f'/api/orders/{self.order.pk}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')

    def test_cancel_shipped_order_fails(self):
        self.order.status = 'shipped'
        self.order.save()
        response = self.client.post(f'/api/orders/{self.order.pk}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class CleanupCommandTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Test', total_stock=10, available_stock=10, reserved_stock=0)

    def test_cleanup(self):
        Reservation.objects.create(
            product=self.product,
            quantity=2,
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        self.product.available_stock -= 2
        self.product.reserved_stock += 2
        self.product.save()
        call_command('cleanup_reservations')
        self.product.refresh_from_db()
        self.assertEqual(self.product.available_stock, 10)
        self.assertEqual(self.product.reserved_stock, 0)
        self.assertEqual(Reservation.objects.count(), 0)
