import json

from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied

from . import handlers


@method_decorator(csrf_exempt, name='dispatch')
class MyWebhookView(View):
    def post(self, request):
        if request.content_type != 'application/json':
            raise PermissionDenied('Content-Type must be application/json.')
        try:
            data = json.loads(request.body)
        except Exception as err:
            raise PermissionDenied(f'Invalid JSON: {err}')

        handler = handlers.MyWebhookHandler(data)
        response_data = handler.handle()
        return JsonResponse(response_data)
