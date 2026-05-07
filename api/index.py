from api.common import get_path
from api.handlers import handle_api


def handler(request):
    path = get_path(request)
    method = getattr(request, "method", "GET")
    return handle_api(method, path, request)
