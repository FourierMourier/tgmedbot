import asyncio
import os
import warnings
from pathlib import Path
import time
import yaml
import fastapi.exceptions
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse

import pydantic

from gpt4all import GPT4All

from typing import Tuple, Optional, Generator, AsyncGenerator

app = FastAPI()

_MAX_TOKENS: int = 256

_FILE_DIR = Path(__file__).absolute().parent
config_path = _FILE_DIR / 'config.yaml'


class LLMServiceConfig(pydantic.BaseModel):
    model_path: pydantic.StrictStr
    template: pydantic.StrictStr


config: Optional[LLMServiceConfig] = None
if config_path.exists():
    print(f"found config at path {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = LLMServiceConfig(**yaml.safe_load(f))


LLM_SERVICE_PORT = os.getenv('LLM_SERVICE_PORT', None)
if LLM_SERVICE_PORT is None:
    LLM_SERVICE_PORT = 8081
else:
    LLM_SERVICE_PORT = int(LLM_SERVICE_PORT)

LLM_SERVICE_HOST = os.getenv('LLM_SERVICE_HOST', "0.0.0.0")


class QueryModel(pydantic.BaseModel):
    user_input: str
    context: str
    max_tokens: Optional[int]


class DummyQueryModel(pydantic.BaseModel):
    user_input: str
    context: str
    max_tokens: Optional[int]
    tokens_per_s: Optional[float]


def _initialize_model(n_threads: Optional[int] = 2) -> Tuple[GPT4All, str]:
    template: str = """
    ### System:
    You are an AI assistant that follows instruction extremely well. Help as much as you can.

    ### User:
    {user_input}

    ### Input:
    {context}

    ### Response:
    """

    model_path_as_env_var = os.getenv("_LLM_SERVICE_MODEL_PATH", None)
    template_as_env_var = os.getenv("_LLM_SERVICE_MODEL_PATH", None)
    if config is not None:
        model_path = config.model_path
        template = config.template or template
    elif (model_path_as_env_var is not None) and (template_as_env_var is not None):
        model_path = model_path_as_env_var
        template = template_as_env_var or template
    else:
        model_path = _FILE_DIR / r"models/orca-mini-3b.ggmlv3.q5_1.bin"

    if Path(model_path).exists() is False:
        raise FileNotFoundError(f"no such file {model_path}")
    # make sure it's string object:
    model_path = str(model_path)
    print(f"using template: {template}")
    print(f"trying to load model from {model_path}...")
    model = GPT4All(model_path, n_threads=n_threads)
    print(f"successfully loaded model")
    return model, template


_LLM_MODEL, _LLM_PROMPT_TEMPLATE = _initialize_model(n_threads=4)


@app.get('/')
async def get_root():
    return JSONResponse({'status': 200})


@app.post("/process_query")
async def process_query(query: QueryModel):
    if len(query.user_input) == 0:
        return JSONResponse({})

    max_tokens = query.max_tokens or _MAX_TOKENS
    prompt = f"Context: \"{query.context}\"\nUser input: {query.user_input}"
    s0 = time.time()
    output = _LLM_MODEL.generate(prompt, max_tokens=max_tokens)
    s1 = time.time()

    results = {
        "output": output,
        "time": (s1 - s0).__round__(2),
        "max_tokens_used": max_tokens,
    }
    return JSONResponse({**results})


# async def get_stream_from_llm(prompt: str, max_tokens: int) -> AsyncGenerator:
def get_stream_from_llm(prompt: str, max_tokens: int) -> Generator:
    """
    You actually can't use sync generators with `async for` so wrap it up into async generator:
    :return:
    """
    for chunk in _LLM_MODEL.generate(prompt, max_tokens=max_tokens, streaming=True):
        # if you do the line below make sure you do chunk = await response.content.read(-1) on the client's side
        #   rather than chunk = await response.content.read(1) so you'll end up having error as str ending
        # yield chunk  # .encode('utf-8')
        # if, on the other hand, you have chunk = await response.content.read(1) do the one below:
        # for c in chunk.encode('utf-8'):
        for c in chunk:
            print(f"yielding \"{c}\" <-- \"{chunk}\"")
            yield c


# @app.post("/process_query_stream")
@app.get("/process_query_stream")
async def process_query_stream(query: QueryModel) -> StreamingResponse:
    if len(query.user_input) == 0:
        return StreamingResponse(iter([]))  # put empty iterator here

    max_tokens = query.max_tokens or _MAX_TOKENS
    # prompt = f"Context: \"{query.context}\"\nUser input: {query.user_input}"
    # prompt = f"Context: \"{query.context}\"\nQ: {query.user_input}"
    prompt = _LLM_PROMPT_TEMPLATE.format(user_input=query.user_input, context=query.context)
    print(f"got prompt:\n{prompt}")
    # https://stackoverflow.com/questions/75740652/fastapi-streamingresponse-not-streaming-with-generator-function
    return StreamingResponse(get_stream_from_llm(prompt, max_tokens), media_type='text/event-stream')


# async def dummy_response_generate(max_tokens: int, tokens_per_s: float) -> AsyncGenerator:  # Generator:
def dummy_response_generate(max_tokens: int, tokens_per_s: float) -> Generator:
    sleep_ms: float = 1 / tokens_per_s
    for i in range(max_tokens):
        time.sleep(sleep_ms)
        yield f"{i}"


# @app.post("/process_query_stream_dummy")
@app.get("/process_query_stream_dummy")
async def process_query_stream_dummy(query: QueryModel):  # DummyQueryModel):
    max_tokens = query.max_tokens or _MAX_TOKENS
    # tokens_per_s: float = query.tokens_per_s or 31.74  # llama2 7b on rtx3070 mobile
    tokens_per_s: float = 31.74
    return StreamingResponse(dummy_response_generate(max_tokens, tokens_per_s), media_type='text/event-stream')


def run_server(host="0.0.0.0", port=8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)  # , reload=True)


if __name__ == "__main__":
    # customize host and port if needed
    run_server(host=LLM_SERVICE_HOST, port=LLM_SERVICE_PORT)
