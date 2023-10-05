import os
import re

from typing import List, Optional


__all__ = ['get_pmid_from_url', 'strip_duplicated_separators']


def get_pmid_from_url(url: str) -> Optional[str]:

    result = os.path.basename(url.strip('/\\'))
    if not result.isdigit():
        return None

    return result


def strip_duplicated_separators(input_string):
    pattern = re.compile(r'(\s*[\r\n]+\s*)+')
    return re.sub(pattern, '\n', input_string)


def _split_string_into_chunks(input_string: str, chunk_length: int, overlap: int, separator: str = "\n\n") -> List[str]:
    chunks = []
    current_chunk = ""

    for line in input_string.split(separator):
        if len(line) == 0:
            continue
        if len(current_chunk + line + separator) <= chunk_length:
            current_chunk += line + separator
        else:
            # strip
            chunks.append(current_chunk.strip())
            current_chunk = line + separator

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
