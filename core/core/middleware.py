import uuid
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

class RequestIDMiddleware(MiddlewareMixin):
    
    def process_request(self, request):    
        request.request_id = SimpleLazyObject(lambda: str(uuid.uuid4()))

    def process_response(self, request, response):
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        if hasattr(response, 'data') and isinstance(response.data, dict):
            response.data['request_id'] = request_id
        else:
            response['X-Request-ID'] = request_id
        return response
