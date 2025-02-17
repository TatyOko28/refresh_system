from django.utils.decorators import sync_and_async_middleware
from django.core.cache import cache
import json
from .clearbit_service import ClearbitService

@sync_and_async_middleware
def EnrichmentMiddleware(get_response):
    async def async_middleware(request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            cache_key = f'user_enrichment_{request.user.id}'
            enriched_data = cache.get(cache_key)

            if not enriched_data and not getattr(request.user, 'clearbit_data', None):
                clearbit_data = await ClearbitService.enrich_user_data(request.user.email)
                if clearbit_data:
                    request.user.clearbit_data = clearbit_data
                    await request.user.asave()
                    cache.set(cache_key, json.dumps(clearbit_data), timeout=86400)

        response = await get_response(request)
        return response

    def sync_middleware(request):
        response = get_response(request)
        return response

    # Django choisit automatiquement la bonne version
    return async_middleware if hasattr(get_response, '__code__') and get_response.__code__.co_flags & 0x80 else sync_middleware
