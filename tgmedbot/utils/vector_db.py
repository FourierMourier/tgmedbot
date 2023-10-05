# import chromadb
import aiohttp
import json
# import ujson
import asyncio
import requests
from urllib.parse import urljoin
from ..constants.common import CHROMA_DB_DIR_PATH, VECTOR_DB_SERVICE_PORT, VECTOR_DB_SERVICE_URL
from ..utils.wrappers import async_time_counter
from typing import List, Optional


__all__ = ['sync_health_check', 'async_health_check', 'sync_get_list_collections', 'async_get_list_collections',
           'sync_process_query', 'async_process_query']


def sync_health_check(method_name: Optional[str] = None) -> bool:
    method_name = method_name or ""
    try:
        response = requests.get(url=urljoin(VECTOR_DB_SERVICE_URL, method_name))
        return response.status_code == requests.codes.OK
    except Exception as E:
        print(f"failed to check chroma with exception {E}")
        return False


async def async_health_check(method_name: Optional[str] = None) -> bool:
    method_name = method_name or ""
    async with aiohttp.ClientSession() as session:
        async with session.get(urljoin(VECTOR_DB_SERVICE_URL, method_name)) as response:
            return response.status != 200


def sync_get_list_collections() -> List[str]:
    method_name: str = "list_collections"
    url = urljoin(VECTOR_DB_SERVICE_URL, method_name)
    try:
        response = requests.get(url=urljoin(VECTOR_DB_SERVICE_URL, method_name))
        if response.status_code == requests.codes.OK:
            return response.json()
    except Exception as E:
        print(f"failed to access {url} chroma with exception {E}")
        return []


async def async_get_list_collections() -> List[str]:
    method_name: str = "list_collections"
    url = urljoin(VECTOR_DB_SERVICE_URL, method_name)

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:  # HTTP OK
                    data = await response.json()
                    return data.get('collections', [])
                else:
                    print(f"Failed to access {url} chroma with status code {response.status}")
                    return []
        except Exception as e:
            print(f"Failed to access {url} chroma with exception {e}")
            return []


def sync_process_query(user_query: str, collection_name: Optional[str] = None, n_results: Optional[int] = None) -> dict:
    method_name: str = "process_query"
    url = urljoin(VECTOR_DB_SERVICE_URL, method_name)
    params = {
        "user_query": user_query,
        "collection_name": collection_name,
        "n_results": n_results
    }
    try:
        response = requests.post(url, json=params, headers={'Content-Type': 'application/json'})
        if response.status_code == requests.codes.OK:
            return response.json()
        else:
            print(f"Failed to access {url} with status code {response.status_code}")
            return {}
    except Exception as e:
        print(f"Failed to access {url} with exception {e}")
        return {}


@async_time_counter()
async def async_process_query(user_query: str, collection_name: Optional[str] = None,
                              n_results: Optional[int] = None) -> dict:
    method_name: str = "process_query"
    url = urljoin(VECTOR_DB_SERVICE_URL, method_name)
    params = {
        "user_query": user_query,
        "collection_name": collection_name,  # if none will refer to food_allergy (ies)
        "n_results": n_results
    }

    headers = {'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        try:
            print(f'accessing {url}...')
            async with session.post(url, json=params, headers=headers) as response:
                print("returning response")
            # async with session.get(url, json=params, headers=headers) as response:
                if response.status == 200:  # HTTP OK
                    data = await response.json()
                    return data
                else:
                    print(f"Failed to access {url} with status code {response.status}")
                    return {}
        except Exception as e:
            print(f"Failed to access {url} with exception {e}")
            return {}
