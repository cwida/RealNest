import concurrent.futures
from concurrent.futures import ProcessPoolExecutor
from datetime import timedelta
from util import *
import tarfile
import pprint
import bz2
import json


def read_json_str(url: str):
    return f"read_json_auto('{url}', sample_size=-1)"


def get_json_schema(duckcon: duckdb.DuckDBPyConnection, url: str):
    return get_schema(duckcon, read_json_str(url))


def get_json_count(duckcon: duckdb.DuckDBPyConnection, url: str):
    return get_count(duckcon, read_json_str(url))


def json_to_json(duckcon: duckdb.DuckDBPyConnection, url: str, schema: Schema, path: str, row_limit: int):
    return to_json(duckcon, schema, path, row_limit, read_json_str(url))


def handle_json_dataset_common(table_dir: Path, jsons_path: Path):
    files = jsons_path / '*.json'
    duckfile = table_dir / 'temp_duck.db'
    with duckdb.connect(duckfile.as_posix()) as duckcon:
        schema = get_json_schema(duckcon, files.as_posix())
        if schema is None:
            delete_folder(table_dir)
            return

        data_file = table_dir / 'data.jsonl'
        json_to_json(duckcon, files.as_posix(), schema, data_file.as_posix(), MAX_ROW_LIMIT)
        rowcount = get_json_count(duckcon, data_file.as_posix())

    if rowcount < MIN_ROW_LIMIT:
        delete_folder(table_dir)
        return
    if rowcount < MAX_ROW_LIMIT:
        print(f"WARNING: Table {table_dir.name} has {rowcount} rows (<{MAX_ROW_LIMIT})", file=sys.stderr)

    delete_folder(jsons_path)

    with open(table_dir / 'schema.json', 'w') as f:
        json.dump(schema, f, default=lambda o: o.__dict__)

    print(f"Exported {rowcount} rows to {table_dir}")

    if duckfile.exists():
        duckfile.unlink()

    compress_table_if_needed(table_dir)


def download_twitter_stream():
    table_dir = create_empty_folder(TABLES_DIR / 'twitter-stream-2023-01')
    url_format = ('https://archive.org/download/archiveteam-twitter-stream-2023-01/twitter-stream-202301{}.tar'
                  '/2023%2F1%2F{}%2F{}%2F{}.json.bz2')

    jsons_path = table_dir / 'json_files'
    jsons_path.mkdir(parents=True, exist_ok=True)
    total_rows = 0
    for date in reversed(range(1, 30)):
        for hour in reversed(range(0, 24)):
            for minute in reversed(range(0, 60)):
                url = url_format.format(str(date).zfill(2), date, hour, minute)
                file = jsons_path / url.split('/')[-1]

                try:
                    do_with_retry(lambda: download_file(url, file), f'download {url}')
                    json_file = file.with_suffix('')
                    print(f"Decompressing {file} to {json_file}")
                    with open(json_file, 'wb') as uncompressed_file, bz2.BZ2File(file, 'rb') as bz2_file:
                        for data in iter(lambda: bz2_file.read(100 * 1024), b''):
                            uncompressed_file.write(data)
                            total_rows += data.count(b'\n')
                    file.unlink()
                    print(f"Total {total_rows} rows so far for twitter-stream-2023-01")
                except Exception as e:
                    print(f"Error handling {url}: {e}", file=sys.stderr)

                if total_rows >= MAX_ROW_LIMIT:
                    break
            if total_rows >= MAX_ROW_LIMIT:
                break
        if total_rows >= MAX_ROW_LIMIT:
            break

    if total_rows < MIN_ROW_LIMIT:
        delete_folder(table_dir)
        return

    handle_json_dataset_common(table_dir, jsons_path)


def download_cord_19():
    table_dir = create_empty_folder(TABLES_DIR / 'cord-19-document_parses')

    file = table_dir / 'document_parses.tar.gz'
    download_s3_file('ai2-semanticscholar-cord-19', 'latest/document_parses.tar.gz', file)

    extract_path = table_dir / 'pdf_json'
    with tarfile.open(file, "r:gz", errorlevel=2) as tar:
        n_extracted = [0]

        def tar_filter(a: tarfile.TarInfo, _):
            if n_extracted[0] >= MAX_ROW_LIMIT:
                raise tarfile.ExtractError("Extracted enough files")

            prefix = 'document_parses/pdf_json/'
            if not a.name.startswith(prefix):
                return None
            a.name = a.name[len(prefix):]
            n_extracted[0] += 1
            return a

        try:
            print(f"Extracting {file} to {extract_path}")
            tar.extractall(extract_path, filter=tar_filter)
        except tarfile.ExtractError:
            pass
    file.unlink()

    handle_json_dataset_common(table_dir, extract_path)


def download_amazon_listings():
    table_dir = create_empty_folder(TABLES_DIR / 'amazon-berkeley-objects-listings')

    json_dir = create_empty_folder(table_dir / 'json_files')
    file = json_dir / 'listings.json.gz'
    download_s3_file('amazon-berkeley-objects', 'listings/listings.json.gz', file)

    decompress_file(file)
    file.unlink()

    handle_json_dataset_common(table_dir, json_dir)


def get_gharchive_url(date: datetime):
    url_format = 'https://data.gharchive.org/{}-{}-{}-{}.json.gz'
    return url_format.format(date.year, str(date.month).zfill(2), str(date.day).zfill(2), date.hour)


def get_gharchive_table_name(date: datetime):
    url = get_gharchive_url(date)
    return 'table_' + url.split('/')[-1].split('.')[0].replace('-', '_')


def create_gharchive_table(main_table_dir: Path, date: datetime):
    url = get_gharchive_url(date)
    print(f"Downloading {url}")
    with duckdb.connect((main_table_dir / (get_gharchive_table_name(date) + ".db")).as_posix()) as duckcon:
        do_with_retry(lambda: duckcon.sql(f"CREATE TABLE {get_gharchive_table_name(date)} AS "
                                          f"SELECT json_extract_string(type, '$') AS type, payload "
                                          f"FROM read_json_auto('{url}', maximum_depth=1)"),
                      f"create table from {url}")


def download_gharchive():
    main_table_dir = create_empty_folder(TABLES_DIR / 'gharchive')
    date = datetime.now(timezone.utc) - timedelta(days=1)
    rowcounts = dict()
    batch_size = 6
    download_more = True
    while download_more:
        orig_date = date
        with ProcessPoolExecutor(max_workers=PROCESS_POOL_SIZE) as executor:
            futures = []
            for _ in range(batch_size):
                futures.append(executor.submit(create_gharchive_table, main_table_dir, date))
                date = date - timedelta(hours=1)

            for future in concurrent.futures.as_completed(futures):
                e = future.exception()
                if e is not None:
                    raise e
        date = orig_date

        for _ in range(batch_size):
            download_more = False
            table_name = get_gharchive_table_name(date)
            db_file = main_table_dir / (table_name + ".db")

            with duckdb.connect(db_file.as_posix()) as duckcon:
                types = duckcon.sql(f"SELECT type, count(*) AS cnt FROM {table_name} GROUP BY type").fetchall()
                for type_, cnt in types:
                    table_dir = TABLES_DIR / f'gharchive-{type_}'
                    table_file = table_dir / 'json_files' / (table_name + '.json')
                    if type_ not in rowcounts:
                        json_structure = duckcon.sql(f"SELECT json_structure(payload) FROM {table_name} "
                                                     f"WHERE type = '{type_}' LIMIT 1").fetchone()[0]
                        if json_structure == '"JSON"':
                            schema = None
                        else:
                            schema = get_schema(duckcon, f"(SELECT unnest(json_transform('{{}}', '{json_structure}')))")
                        if schema is None:
                            rowcounts[type_] = -1
                            continue

                        rowcounts[type_] = 0
                        create_empty_folder(table_dir)
                        table_file.parent.mkdir(parents=True, exist_ok=True)
                    if rowcounts[type_] == -1 or rowcounts[type_] >= MAX_ROW_LIMIT:
                        continue

                    cnt = min(cnt, MAX_ROW_LIMIT - rowcounts[type_])
                    rowcounts[type_] += cnt
                    if rowcounts[type_] < MAX_ROW_LIMIT and type_ not in GHARCHIVE_SHORT_TABLE_LIST:
                        download_more = True

                    print(f"Exporting events of {type_} to {table_file}")
                    duckcon.sql(f"COPY (SELECT payload FROM {table_name} WHERE type = '{type_}' LIMIT {cnt}) "
                                f"TO '{table_file}' (FORMAT csv, HEADER false, QUOTE '', ESCAPE '')")

                    if rowcounts[type_] >= MAX_ROW_LIMIT:
                        handle_json_dataset_common(table_dir, table_file.parent)

            db_file.unlink()
            date = date - timedelta(hours=1)
        print(f"Total rows so far for gharchive event types: {pprint.pformat(rowcounts, sort_dicts=False)}")

    for type_, cnt in rowcounts.items():
        if cnt == -1 or cnt < MIN_ROW_LIMIT or cnt >= MAX_ROW_LIMIT:
            continue
        table_dir = TABLES_DIR / f'gharchive-{type_}'
        handle_json_dataset_common(table_dir, table_dir / 'json_files')

    delete_folder(main_table_dir)
