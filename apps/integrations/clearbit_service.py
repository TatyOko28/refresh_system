import aiohttp
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

class ClearbitService:
    BASE_URL = 'https://person.clearbit.com/v2/people/find'

    @staticmethod
    async def enrich_user_data(email: str) -> dict:
        """
        Enrich user data using Clearbit API
        """
        headers = {
            'Authorization': f'Bearer {settings.CLEARBIT_API_KEY}',
            'Content-Type': 'application/json'
        }
        params = {'email': email}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    ClearbitService.BASE_URL,
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        logger.info(f"No Clearbit data found for email: {email}")
                        return None
                    else:
                        logger.error(
                            f"Clearbit API error: {response.status} for email: {email}"
                        )
                        return None
        except Exception as e:
            logger.error(f"Error enriching user data with Clearbit: {str(e)}")
            return None

