from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import django
from scripts.populate import populate_database

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.core.settings')
django.setup()


class HealthCheckAPI(APIView):
    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)


class PopulateAPI(APIView):
    def post(self, request):
        try:
            populate_database()
            return Response({"message": "Database populated successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)