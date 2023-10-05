import chromadb
from constants import CHROMA_DB_DIR_PATH

from typing import List, Optional


def get_chroma_client() -> chromadb.PersistentClient:
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR_PATH))
    return chroma_client


def list_chroma_collections(chroma_client: Optional[chromadb.PersistentClient] = None) -> List[str]:
    if chroma_client is None:
        chroma_client = get_chroma_client()

    return [c.name for c in chroma_client.list_collections()]


def get_collection(name: Optional[str] = None, chroma_client: Optional[chromadb.PersistentClient] = None) \
        -> Optional[chromadb.api.Collection]:
    name = name or "food_allergies"  # TODO: remove later such hardcoded and refer to that as some constant

    if chroma_client is None:
        chroma_client = get_chroma_client()

    collection = None
    for c in chroma_client.list_collections():
        if c.name == name:
            collection = c

    return collection
