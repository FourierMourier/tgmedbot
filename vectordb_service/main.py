import os
import chromadb
import fastapi.exceptions
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from constants import CHROMA_DB_DIR_PATH
from utils.common import list_chroma_collections, get_collection, get_chroma_client
from schemas import QueryModel
from typing import List, Dict, Optional


app = FastAPI()

VECTOR_DB_SERVICE_PORT = os.getenv('VECTOR_DB_SERVICE_PORT', None)
if VECTOR_DB_SERVICE_PORT is None:
    VECTOR_DB_SERVICE_PORT = 8000
else:
    VECTOR_DB_SERVICE_PORT = int(VECTOR_DB_SERVICE_PORT)

VECTOR_DB_SERVICE_HOST = os.getenv('VECTOR_DB_SERVICE_HOST', "0.0.0.0")


if len(list_chroma_collections()) == 0:
    raise RuntimeError((f"Cannot use this service: please first create vector database at required path "
                        f"{CHROMA_DB_DIR_PATH.absolute()} and fill it with some data"))


class ChromaCollectionManager:
    def __init__(self):
        self._collection_map: Dict[str, chromadb.api.Collection] = {}
        self._client = get_chroma_client()

    @property
    def collection_map(self) -> Dict[str, chromadb.api.Collection]:
        return self._collection_map

    @property
    def client(self):
        return self._client

    def __getitem__(self, key: str) -> Optional[chromadb.api.Collection]:
        return self.collection_map.get(key, None)

    def __setitem__(self, key, value):
        print(f"setting {key} -> {value}")
        self._collection_map[key] = value


collectionManager = ChromaCollectionManager()
for collection_name in list_chroma_collections():
    collectionManager[collection_name] = get_collection(collection_name, collectionManager.client)


@app.get('/')
async def get_root():
    return JSONResponse({'status': 200})


@app.get('/list_collections')
async def get_list_collections():
    return JSONResponse({'collections': list_chroma_collections()})


@app.post("/process_query")
async def process_query(query: QueryModel):
    collection_name = query.collection_name or "food_allergies"
    collection = collectionManager[collection_name]
    if collection is None:
        raise fastapi.exceptions.HTTPException(status_code=404,
                                               detail=f"collection={query.collection_name} wasn't found")
    n_results = query.n_results or 2  # why 2, maybe 3??
    results = collection.query(query_texts=[query.user_query], n_results=n_results)
    return JSONResponse({**results})


def run_server(host="0.0.0.0", port=8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)  # , reload=True)


if __name__ == "__main__":
    # customize host and port if needed
    run_server(host=VECTOR_DB_SERVICE_HOST, port=VECTOR_DB_SERVICE_PORT)
