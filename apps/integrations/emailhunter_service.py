import aiohttp
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EmailHunterService:
    BASE_URL = 'https://api.hunter.io/v2/email-verifier'

    @staticmethod
    async def verify_email(email: str) -> dict:
        """
        Verify email using Email Hunter API
        """
        params = {
            'email': email,
            'api_key': settings.EMAILHUNTER_API_KEY
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    EmailHunterService.BASE_URL,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'status': data['data']['status'],
                            'score': data['data']['score'],
                            'is_valid': data['data']['status'] == 'valid'
                        }
                    else:
                        logger.error(
                            f"EmailHunter API error: {response.status} for email: {email}"
                        )
                        return None
        except Exception as e:
            logger.error(f"Error verifying email with EmailHunter: {str(e)}")
            return None

