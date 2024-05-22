from pathlib import Path
from datetime import datetime, timezone
import os

# Tables with fewer rows will be ignored
MIN_ROW_LIMIT = int(os.getenv('MIN_ROW_LIMIT', 50 * 1024))

# Tables with more rows will be truncated
MAX_ROW_LIMIT = int(os.getenv('MAX_ROW_LIMIT', 64 * 1024))

# Folder to store the data in. Will be cleared if it already exists!
TABLES_DIR = Path(os.getenv('TABLES_DIR', f'./tables_{MAX_ROW_LIMIT}')).resolve()

# Whether to compress the data with gzip
COMPRESS = bool(os.getenv('COMPRESS', True))

# Whether to keep the uncompressed data
KEEP_ORIGINAL = bool(os.getenv('KEEP_ORIGINAL', False))

# Number of processes to use while downloading and processing data
PROCESS_POOL_SIZE = int(os.getenv('PROCESS_POOL_SIZE', os.cpu_count() or 1))

# Set of tables from GitHub Archive dataset that are allowed to be shorter than MAX_ROW_LIMIT (otherwise, it takes too
# long)
GHARCHIVE_SHORT_TABLE_LIST = {
    'GollumEvent', 'CommitCommentEvent',
    # 'MemberEvent', 'ReleaseEvent',
}

print(f"""CONFIG:
MIN_ROW_LIMIT: {MIN_ROW_LIMIT}
MAX_ROW_LIMIT: {MAX_ROW_LIMIT}
TABLES_DIR: {TABLES_DIR}
COMPRESS: {COMPRESS}
KEEP_ORIGINAL: {KEEP_ORIGINAL}
PROCESS_POOL_SIZE: {PROCESS_POOL_SIZE}
GHARCHIVE_SHORT_TABLE_LIST: {GHARCHIVE_SHORT_TABLE_LIST}

CURRENT TIME: {datetime.now(timezone.utc).isoformat()}
""")
