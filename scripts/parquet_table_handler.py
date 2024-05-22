from concurrent.futures import ThreadPoolExecutor
from util import *
import concurrent.futures
import json
import re


def read_parquet_str(url: str):
    return f"read_parquet('{url}')"


def get_parquet_metadata(duckcon: duckdb.DuckDBPyConnection, url: str):
    return get_metadata(duckcon, read_parquet_str(url))


def parquet_to_json(duckcon: duckdb.DuckDBPyConnection, url: str, schema: Schema, path: str, row_limit: int):
    return to_json(duckcon, schema, path, row_limit, read_parquet_str(url))


def handle_parquet_table(key: str, urls: list[str]):
    if re.fullmatch('aws-roda-hcls-datalake-opentargets_latest-epmccooccurrences_[0-9a-f]*', key):
        key = 'aws-roda-hcls-datalake-opentargets_latest-epmccooccurrences'
    table_dir = create_empty_folder(TABLES_DIR / key)

    duckfile = table_dir / 'temp_duck.db'
    with duckdb.connect(duckfile.as_posix()) as duckcon:
        try:
            total_rows = 0
            file_cnt = 0
            merged_schema = Schema([])

            jsons_dir = create_empty_folder(table_dir / 'jsons')
            with ThreadPoolExecutor() as executor:
                futures = []
                n_no_nested = 0
                for url in reversed(urls):
                    result = get_parquet_metadata(duckcon, url)
                    if result is None:
                        n_no_nested += 1
                        if n_no_nested >= 10:
                            break
                        continue

                    result.rowcount = min(result.rowcount, MAX_ROW_LIMIT - total_rows)
                    file = jsons_dir / f'{file_cnt}.jsonl'
                    futures.append(
                        executor.submit(parquet_to_json, duckcon.cursor(), url, result.schema, file, result.rowcount))
                    file_cnt += 1

                    merged_schema.merge(result.schema)
                    total_rows += result.rowcount
                    if total_rows >= MAX_ROW_LIMIT:
                        break

                    print(f"Total {total_rows} rows so far for {key}")

                if total_rows < MIN_ROW_LIMIT:
                    executor.shutdown(cancel_futures=True)
                    duckcon.close()
                    delete_folder(table_dir)
                    return
                if total_rows < MAX_ROW_LIMIT:
                    print(f"WARNING: Table {key} has {total_rows} rows (<{MAX_ROW_LIMIT})", file=sys.stderr)

                for future in concurrent.futures.as_completed(futures):
                    e = future.exception()
                    if e is not None:
                        raise e

            with open(table_dir / 'data.jsonl', 'w') as f:
                for i in range(file_cnt):
                    with open(jsons_dir / f'{i}.jsonl', 'r') as g:
                        content = g.read()
                        if key == 'aws-roda-hcls-datalake-gnomad-sites':
                            content = content.replace('[Infinity]', '[0.0]')
                        if key == 'hep-adl-ethz-Run2012B_SingleMu':
                            content = content.replace('"relIso_all":NaN', '"relIso_all":0.0')
                        f.write(content)
            delete_folder(jsons_dir)

            with open(table_dir / 'schema.json', 'w') as f:
                json.dump(merged_schema, f, default=lambda o: o.__dict__)

            print(f"Exported {total_rows} rows to {table_dir}")
        except Exception as e:
            print(f"Unexpected error for {key}", e, file=sys.stderr)

    if duckfile.exists():
        duckfile.unlink()

    compress_table_if_needed(table_dir)
