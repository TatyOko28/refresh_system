import pytest
from unittest.mock import patch, AsyncMock
from apps.integrations.clearbit_service import ClearbitService
from apps.integrations.emailhunter_service import EmailHunterService


@pytest.mark.asyncio
class TestIntegrationServices:
    async def test_clearbit_enrichment_success(self):
        mock_response = {
            'name': {'givenName': 'John', 'familyName': 'Doe'},
            'email': 'test@example.com',
            'employment': {'title': 'Developer'}
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_context = AsyncMock()
            mock_context.status = 200
            mock_context.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_context

            result = await ClearbitService.enrich_user_data('test@example.com')
            assert result == mock_response

    async def test_emailhunter_verification_success(self):
        mock_response = {
            'data': {
                'status': 'valid',
                'score': 90,
                'email': 'test@example.com'
            }
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_context = AsyncMock()
            mock_context.status = 200
            mock_context.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_context

            result = await EmailHunterService.verify_email('test@example.com')
            assert result['is_valid'] is True
            assert 'score' in result