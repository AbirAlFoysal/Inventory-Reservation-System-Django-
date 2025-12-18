from rest_framework.renderers import JSONRenderer

class RequestIDJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        request = renderer_context.get("request")
        response = renderer_context.get("response")

        if not request or not hasattr(request, "request_id"):
            return super().render(data, accepted_media_type, renderer_context)

        request_id = request.request_id

        if isinstance(data, dict):
            data["request_id"] = request_id

        return super().render(data, accepted_media_type, renderer_context)
