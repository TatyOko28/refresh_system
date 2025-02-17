import json
from django.core.cache import cache
from asgiref.sync import async_to_sync
from django.http import HttpRequest, HttpResponse
from typing import Callable

class EnrichmentMiddleware:
    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Don't wrap with async_to_sync - just call directly
        return self.get_response(request)

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable,
        view_args: tuple,
        view_kwargs: dict
    ):
        if hasattr(view_func, 'enrich_user_data') and request.user.is_authenticated:
            cache_key = f'user_enrichment_{request.user.id}'
            enriched_data = cache.get(cache_key)
            
            if not enriched_data and not request.user.clearbit_data:
                from .clearbit_service import ClearbitService
                # Only wrap the Clearbit service call which we know is async
                clearbit_data = async_to_sync(ClearbitService.enrich_user_data)(request.user.email)
                if clearbit_data:
                    request.user.clearbit_data = clearbit_data
                    request.user.save()  
                    cache.set(cache_key, json.dumps(clearbit_data), timeout=86400)
        return None