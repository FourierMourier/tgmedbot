# import chromadb
import aiohttp
import json
# import ujson
import asyncio
import requests
from urllib.parse import urljoin
from ..constants.common import LLM_SERVICE_URL
from ..utils.wrappers import async_time_counter

from typing import AsyncGenerator, List, Optional


__all__ = ['sync_llm_health_check', 'async_llm_health_check', 'async_llm_process_query', 'async_process_query_stream',
           'LLM_PROCESS_QUERY_STREAM_URL', 'DUMMY_PROCESS_QUERY_STREAM_URL']


LLM_PROCESS_QUERY_STREAM_URL = urljoin(LLM_SERVICE_URL, "process_query_stream")
DUMMY_PROCESS_QUERY_STREAM_URL = urljoin(LLM_SERVICE_URL, "process_query_stream_dummy")


def sync_llm_health_check(method_name: Optional[str] = None) -> bool:
    method_name = method_name or ""
    try:
        response = requests.get(url=urljoin(LLM_SERVICE_URL, method_name))
        return response.status_code == requests.codes.OK
    except Exception as E:
        print(f"failed to check llm service with exception {E}")
        return False


async def async_llm_health_check(method_name: Optional[str] = None) -> bool:
    method_name = method_name or ""
    async with aiohttp.ClientSession() as session:
        async with session.get(urljoin(LLM_SERVICE_URL, method_name)) as response:
            return response.status != 200


@async_time_counter()
async def async_llm_process_query(user_input: str,
                                  context: str,
                                  max_tokens: Optional[int] = None, ) -> dict:
    method_name: str = "process_query"
    url = urljoin(LLM_SERVICE_URL, method_name)
    params = {
        "user_input": user_input,
        "context": context,  # if none will refer to food_allergy (ies)
        "max_tokens": max_tokens
    }
    headers = {'Content-Type': 'application/json'}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=params, headers=headers) as response:
                if response.status == 200:  # HTTP OK
                    data = await response.json()
                    return data
                else:
                    print(f"Failed to access {url} with status code {response.status}")
                    return {}
        except Exception as e:
            print(f"Failed to access {url} with exception {e}")
            return {}


async def async_process_query_stream(url, user_input: str, context: str, max_tokens: int) -> AsyncGenerator:
    params = {
        "user_input": user_input,
        "context": context,
        "max_tokens": max_tokens
    }
    headers = {'Content-Type': 'application/json'}

    async with aiohttp.ClientSession() as session:
        # async with session.post(url, json=params, headers=headers, chunked=True) as response:
        async with session.get(url, json=params, headers=headers, chunked=True) as response:
            async for chunk in response.content.iter_any():
                if not chunk:
                    break
                yield chunk.decode('utf-8')
