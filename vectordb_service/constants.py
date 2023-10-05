from pathlib import Path


__all__ = ['CHROMA_DB_DIR_PATH']


PROJECT_ROOT = Path(__file__).parents[1]
CHROMA_DB_DIR_PATH = PROJECT_ROOT / 'chroma'
