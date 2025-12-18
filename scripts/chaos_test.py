import os
import sys
import django
from concurrent.futures import ThreadPoolExecutor
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inventory.models import Product

BASE_URL = 'http://127.0.0.1:8000/api' 

def attempt_reservation(product_id):
    try:
        response = requests.post(
            f'{BASE_URL}/reservations/',
            json={'product': int(product_id), 'quantity': 1},
            timeout=5
        )
        print(f"Response status: {response.status_code}, text: {response.text}")
        return response.status_code == 201
    except Exception as e:
        print(f"Exception: {e}")
        return False

def main():
    product, created = Product.objects.get_or_create(
        name='Test Product',
        defaults={'total_stock': 5, 'available_stock': 5, 'reserved_stock': 0}
    )
    if not created:
        product.total_stock = 5
        product.available_stock = 5
        product.reserved_stock = 0
        product.save()

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(attempt_reservation, product.pk) for _ in range(50)]
        results = [f.result() for f in futures]

    succeeded = sum(results)
    failed = len(results) - succeeded

    product.refresh_from_db()
    print("Chaos Test Results")
    print("-----------------")
    print(f"Succeeded: {succeeded}")
    print(f"Failed: {failed}")
    print(f"Final available_stock: {product.available_stock}")
    print(f"Final reserved_stock: {product.reserved_stock}")
    print(f"Total stock: {product.total_stock}")

    assert succeeded == product.total_stock, "Exactly total_stock must succeed!"

if __name__ == "__main__":
    main()
