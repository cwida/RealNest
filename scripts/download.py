from parquet_table_handler import *
from json_table_handler import *
from botocore import UNSIGNED
from botocore.client import Config
import boto3
import typing
import re


@dataclass
class TableMetadata:
    url_regex: str | re.Pattern
    table_key_format: str
    s3_prefix: str | None = None
    format: str | None = None


@dataclass
class S3Dataset:
    tables: list[TableMetadata]
    s3_prefix: str = ''

    def __init__(self, tables: list[dict], s3_prefix: str = ''):
        self.s3_prefix = s3_prefix
        self.tables = [TableMetadata(**table) for table in tables]


def main():
    with open('parquet_metadata.json', 'r') as f:
        json_dict: dict = json.load(f)
        datasets: dict[str, S3Dataset] = {dataset: S3Dataset(**json_dict[dataset]) for dataset in json_dict}

    create_empty_folder(TABLES_DIR)
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    with ProcessPoolExecutor(max_workers=PROCESS_POOL_SIZE) as p:
        pool_results = [
            p.submit(download_cord_19),
            p.submit(download_gharchive),
            p.submit(download_amazon_listings),
            p.submit(download_twitter_stream),
        ]
        for dataset_name in datasets:
            print(f"Handling dataset {dataset_name}")
            try:
                tables = datasets[dataset_name].tables

                for table in tables:
                    if table.format is None:
                        table.format = 'parquet' if typing.cast(str, table.url_regex).endswith('parquet') else 'json'
                    table.url_regex = re.compile(table.url_regex)

                table_urls: dict[str, dict[str, list[str] | str]] = dict()

                traversed_urls = 0
                for url in traverse_s3_folder(s3, dataset_name, datasets[dataset_name].s3_prefix):
                    traversed_urls += 1
                    if traversed_urls % 10000 == 0:
                        print(f"Traversed {traversed_urls} URLs so far")

                    for table in tables:
                        match = table.url_regex.fullmatch(url)
                        if match:
                            table_key = f"{dataset_name}-{table.table_key_format.format(*match.groups())}"
                            if table_key not in table_urls:
                                table_urls[table_key] = {'urls': [], 'format': table.format}

                            table_urls[table_key]['urls'].append(url)
                            break
                print(f"Done traversing URLs in bucket. Total URLs: {traversed_urls}")

                for key in table_urls:
                    pool_results.append(p.submit(handle_parquet_table, key, table_urls[key]['urls']))
            except Exception as e:
                print(f"Unexpected error for {dataset_name}", e, file=sys.stderr)

        while True:
            time.sleep(5)
            done = [result.done() for result in pool_results]
            if all(done):
                for future in concurrent.futures.as_completed(pool_results):
                    e = future.exception()
                    if e is not None:
                        raise e
                break

            print(f"{len(pool_results) - sum(done)} tables remaining...")
    print("Done!")


if __name__ == '__main__':
    main()
