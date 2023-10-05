from typing import List


__all__ = ['PubMedDataConstants']


class PubMedDataConstants:
    # ----- df constants -----
    ABSTRACT_COLUMN: str = 'abstract'
    # since we can be sure that 1 and only 1 article can have the same pmid we can assign ids based on that value
    ID_COLUMN: str = 'pmid'
    #
    NON_NA_SUBSET_COLUMNS: List[str] = [ID_COLUMN, ABSTRACT_COLUMN]
