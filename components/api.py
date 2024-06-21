import aiohttp
import logging

logger = logging.getLogger(__name__)

async def search_company(session, company_name):
    endpoint = 'https://api.brandfetch.io/v2/search'
    url = f"{endpoint}/{company_name}"
    headers = {
        'accept': 'application/json',
        'Referer': 'http://localhost:8501'
    }
    try:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            if data:
                return data[0] if isinstance(data, list) else data
            else:
                return {"error": "No brands found"}
    except aiohttp.ClientError as e:
        logger.error(f"Error searching for {company_name}: {e}")
        return {"error": str(e)}

async def fetch_brand_details(session, domain, api_key):
    endpoint = f'https://api.brandfetch.io/v2/brands/{domain}'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    try:
        async with session.get(endpoint, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching details for domain {domain}: {e}")
        return {"error": str(e)}
