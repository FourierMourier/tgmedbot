import os
import time
from pathlib import Path

import pyarrow
import numpy as np
import pandas as pd

import chromadb
import pydantic

from tgmedbot.constants import *
from tgmedbot.utils.common import load_config
from tgmedbot.utils.documents import *

from langchain.document_loaders import DataFrameLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter

from tqdm import tqdm

import warnings
from typing import List, Dict


class CreateDbConfigModel(pydantic.BaseModel):
    df_path: str
    collection_name: str


def main():
    delete_collection_if_exists: bool = False  # True
    chunk_size: int = 256
    # separator: str = "\n"
    # separator: str = ". "

    separators: List[str] = ["\n\n", "\n", ". "]

    overlap_fraction: float = 0.10
    stride: int = 16

    current_file = Path(__file__)
    configs_dir = current_file.parents[0] / 'configs'
    config_filepath = configs_dir / (current_file.stem + '.yaml')

    config = CreateDbConfigModel(**load_config(config_filepath))

    persist_directory = CHROMA_DB_DIR_PATH
    persist_directory.parents[0].mkdir(exist_ok=True)
    persist_directory.mkdir(exist_ok=True)
    #  https://docs.trychroma.com/migration
    chroma_client = chromadb.PersistentClient(path=str(persist_directory))
    #
    chroma_client.__dir__()
    #
    collection_name = config.collection_name
    df = pd.read_parquet(config.df_path)
    #
    pmid_none_mask: pd.Series = df[PubMedDataConstants.ID_COLUMN].isna()
    existing_abstract_mask: pd.Series = df[PubMedDataConstants.ABSTRACT_COLUMN].notna()  # != .isna()
    print(f"rows with no id: {pmid_none_mask.sum()}")
    have_abstract_but_no_id: pd.Series = pmid_none_mask & existing_abstract_mask
    print(f"rows with no id but with abstract: {have_abstract_but_no_id.sum()}")
    df.loc[have_abstract_but_no_id, PubMedDataConstants.ID_COLUMN] = df.loc[have_abstract_but_no_id, 'url'].apply(lambda x: get_pmid_from_url(x))
    print(f"{df.loc[have_abstract_but_no_id, PubMedDataConstants.ID_COLUMN].isna().sum()} rows are still with no id")
    prev_len: int = len(df)
    df = df.dropna(subset=list(PubMedDataConstants.NON_NA_SUBSET_COLUMNS))
    print(f"{prev_len - len(df)} rows were dropped based on null {PubMedDataConstants.NON_NA_SUBSET_COLUMNS} columns")
    # but we may still have some duplicated ids and that may cause `chromadb.errors.DuplicateIDError`
    #   right before the very end so check this out
    # id_duplicated_mask = df[PubMedDataConstants.ID_COLUMN].duplicated()
    # duplicated_ids: List[int] = df.loc[id_duplicated_mask, PubMedDataConstants.ID_COLUMN].tolist()
    # df[df[PubMedDataConstants.ID_COLUMN].isin(duplicated_ids)]
    prev_len = len(df)
    df = df.drop_duplicates(subset=list(PubMedDataConstants.NON_NA_SUBSET_COLUMNS))
    print(f"{prev_len - len(df)} rows were removed based on duplicates for {PubMedDataConstants.NON_NA_SUBSET_COLUMNS} columns")

    # metadata_columns: List[str] = [col for col in df.columns if col not in PubMedDataConstants.NON_NA_SUBSET_COLUMNS]

    collection_names = [c.name for c in chroma_client.list_collections()]
    
    db_exists: bool = len(collection_names) and collection_name in collection_names

    collection = None
    if db_exists:
        print(f"collection {collection_name} already in chromadb")
        for c in chroma_client.list_collections():
            if c.name == collection_name:
                collection = c
    elif db_exists and delete_collection_if_exists:
        chroma_client.delete_collection(name=collection_name)
        db_exists = False

    if not db_exists:
        collection = chroma_client.create_collection(name=collection_name)

    assert collection is not None, f"check chromadb/if-statements"

    # remove duplicated symbols like \n:
    df[PubMedDataConstants.ABSTRACT_COLUMN] = \
        df[PubMedDataConstants.ABSTRACT_COLUMN].apply(lambda x: strip_duplicated_separators(x))

    ## how we'd do that manually:
    # ids: List[str] = df[PubMedDataConstants.ID_COLUMN].tolist()
    # documents: List[str] = df[PubMedDataConstants.ABSTRACT_COLUMN].tolist()
    # metadatas: List[Dict[str, Any]] = [row.dropna().to_dict() for _, row in df[metadata_columns].iterrows()]
    ## using langchain
    df_loader = DataFrameLoader(df, page_content_column=PubMedDataConstants.ABSTRACT_COLUMN)
    df_document = df_loader.load()
    # about chunk_overlap:
    #   https://js.langchain.com/docs/modules/data_connection/document_transformers/#:~:text=chunkOverlap%20specifies%20how%20much%20overlap,text%20isn't%20split%20weirdly.
    chunk_overlap: int = round(overlap_fraction * chunk_size / stride) * stride
    chunk_overlap = chunk_overlap if chunk_overlap > 0 else stride
    print(f"chunk_overlap={chunk_overlap} || chunk_size={chunk_size}")
    # %%
    round(round(overlap_fraction * chunk_size) / stride) * stride
    # %%
    # text_splitter = CharacterTextSplitter(separator, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    text_splitter = RecursiveCharacterTextSplitter(separators, keep_separator=False,
                                                   chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    texts = text_splitter.split_documents(df_document)

    id_current_counter_map: Dict[str, int] = {}
    #
    documents = []
    metadatas = []
    ids = []
    #
    pbar = tqdm(range(len(texts)), total=len(texts))
    for text_pos in pbar:
        curr_doc = texts[text_pos]
        metadata = curr_doc.metadata
        curr_doc_id: str = metadata[PubMedDataConstants.ID_COLUMN]
        pbar.set_postfix({"processing pmid": f"{curr_doc_id}"})

        if curr_doc_id not in id_current_counter_map:
            id_current_counter_map[curr_doc_id] = 0
        else:
            id_current_counter_map[curr_doc_id] += 1

        curr_chunk = id_current_counter_map[curr_doc_id]
        metadata['chunk'] = curr_chunk
        # prevent None in the values:
        metadata = pd.Series(metadata).dropna().to_dict()

        curr_extended_id: str = f"{curr_doc_id}-{curr_chunk}"
        ids.append(curr_extended_id)
        documents.append(curr_doc.page_content)
        metadatas.append(metadata)

    tmp_str = '\n'.join(('*' * 50,) * 3)
    print(tmp_str)
    print(f"{len(df_document)} -> {len(documents)}")
    print(tmp_str)
    s0: float = time.time()
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )
    s1 = time.time()
    print(f"inserted {len(documents)} documents in {s1 - s0:.3f} seconds")


if __name__ == '__main__':
    main()
