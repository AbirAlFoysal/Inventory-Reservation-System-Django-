import uuid
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("request")

class RequestIDMiddleware(MiddlewareMixin):
    HEADER_NAME = "X-Request-ID"

    def process_request(self, request):
        request.request_id = str(uuid.uuid4())

    def process_response(self, request, response):
        request_id = getattr(request, "request_id", "-")

        response[self.HEADER_NAME] = request_id

        logger.info(
            "completed",
            extra={"request_id": request_id},
        )

        return response
