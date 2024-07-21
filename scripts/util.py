from schema import Schema
from dataclasses import dataclass, astuple
from botocore import UNSIGNED
from botocore.client import Config
from config import *
import builtins
import boto3
import sys
import time
import urllib.request
import shutil
import duckdb
import gzip

print = lambda *args, **kwargs: builtins.print(f'{datetime.now(timezone.utc).isoformat()}:', *args, **kwargs,
                                               flush=True)


def do_with_retry(func, msg):
    n_repeat = 0
    while True:
        try:
            return func()
        except Exception as e:
            n_repeat += 1
            if n_repeat == 5:
                raise e
            print(f"Retrying operation {msg} (Error: {e})", file=sys.stderr)
            time.sleep(5)


def compress_table_if_needed(table_dir: Path):
    data_file = table_dir / 'data.jsonl'
    if not data_file.exists() or not COMPRESS:
        return

    compress_file(data_file)
    if not KEEP_ORIGINAL:
        data_file.unlink()


def compress_file(data_file: Path):
    compressed_file = data_file.with_suffix(data_file.suffix + '.gz')
    print(f"Compressing {data_file} to {compressed_file}")
    with open(data_file, 'rb') as f_in, gzip.open(compressed_file, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)


def decompress_file(compressed_file: Path):
    decompressed_file = compressed_file.with_suffix('')
    print(f"Decompressing {compressed_file} to {decompressed_file}")
    with gzip.open(compressed_file, 'rb') as f_in, decompressed_file.open('wb') as f_out:
        shutil.copyfileobj(f_in, f_out)


def download_file(url, file):
    print(f"Downloading {url} to {file}")
    req = urllib.request.Request(url, headers={'User-Agent': ""})
    with urllib.request.urlopen(req) as response, open(file, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


def download_s3_file(bucket_name, key, file):
    print(f"Downloading s3://{bucket_name}/{key} to {file}")
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED), region_name='us-east-1')
    with open(file, 'wb') as data:
        s3.download_fileobj(bucket_name, key, data)


def traverse_s3_folder(s3, bucket, prefix):
    paginator = s3.get_paginator('list_objects_v2')

    for response in do_with_retry(lambda: paginator.paginate(Bucket=bucket, Prefix=prefix),
                                  f'list S3 objects in {bucket}/{prefix}'):
        contents = [c['Key'] for c in response.get('Contents', [])]
        for content in contents:
            yield f"s3://{bucket}/{content}"


def delete_folder(folder: Path):
    if folder.exists():
        shutil.rmtree(folder)


def create_empty_folder(folder: Path):
    delete_folder(folder)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


@dataclass
class Metadata:
    rowcount: int
    schema: Schema

    def __iter__(self):
        return iter(astuple(self))


def get_metadata(duckcon: duckdb.DuckDBPyConnection, from_: str):
    try:
        schema = get_schema(duckcon, from_)

        if schema is not None:
            rowcount = get_count(duckcon, from_)
            return Metadata(rowcount, schema)
    except Exception as e:
        print(f"Unexpected error for {from_}", e, file=sys.stderr)


def get_count(duckcon: duckdb.DuckDBPyConnection, from_: str):
    try:
        print(f"Counting {from_}")
        rowcount = do_with_retry(lambda: duckcon.sql(f"SELECT COUNT(*) FROM {from_}").fetchone()[0],
                                 f'count {from_}')
        return rowcount
    except Exception as e:
        print(f"Unexpected error for {from_}", e, file=sys.stderr)


def get_schema(duckcon: duckdb.DuckDBPyConnection, from_: str):
    try:
        print(f"Reading schema of {from_}")
        try:
            columns = do_with_retry(lambda: duckcon.sql(f"DESCRIBE SELECT * FROM {from_}").fetchnumpy(),
                                    f'read {from_}')
        except Exception as e:
            print(f"Could not read {from_}", e, file=sys.stderr)
            return

        nested_cols = []
        for colname, typestr in zip(columns["column_name"], columns["column_type"]):
            type = duckdb.type(typestr)
            try:
                _ = type.children
                if type.id != 'decimal':
                    nested_cols.append((colname, type))
            except duckdb.InvalidInputException:
                pass

        if nested_cols:
            return Schema(nested_cols)
        else:
            print(f"No nested columns found in {from_}")
    except Exception as e:
        print(f"Unexpected error for {from_}", e, file=sys.stderr)


def to_json(duckcon: duckdb.DuckDBPyConnection, schema: Schema, path: str, row_limit: int, from_: str):
    print(f"Selecting nested columns from {from_}")
    select_fields = ', '.join(['"' + col.name + '"' for col in schema.columns])
    try:
        do_with_retry(
            lambda: duckcon.sql(f"COPY (SELECT {select_fields} FROM {from_} LIMIT {row_limit})"
                                f"TO '{path}'"), f'select nested columns from {from_} to {path}')
    except Exception as e:
        raise Exception(f"Error selecting nested columns from {from_}: {e}")
