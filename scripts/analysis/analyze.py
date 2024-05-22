from concurrent.futures import ProcessPoolExecutor
from dataclasses import field
from util import *
from analysis_util import *
from schema import Schema
import concurrent
import json


@dataclass
class SchemaColumnStats:
    path: str = ''
    type: str = ''
    depth: int = 0
    list_depth: int = 0
    simple_subfields: int = 0


@dataclass
class SchemaStats:
    col_stats: list[SchemaColumnStats] = field(default_factory=lambda: ([]))
    nested_type_counts: dict[str, int] = field(default_factory=lambda: ({}))
    simple_type_counts: dict[str, int] = field(default_factory=lambda: ({}))


@dataclass
class ColumnStats:
    path: str = ''
    type: str = ''
    row_count: int = 0
    null_percentage: float | None = None
    unique_percentage: float | None = None
    # Below are for lists & strings only
    min_length: int | None = None
    avg_length: float | None = None
    max_length: int | None = None
    empty_percentage: float | None = None


@dataclass
class DataStats:
    row_count: int = 0
    col_stats: list[ColumnStats] = field(default_factory=lambda: ([]))


@dataclass
class Stats:
    dataset: str
    name: str
    jsonl_kb: int
    jsonl_gz_kb: int
    schema: SchemaStats
    data: DataStats

    def merge(self, other: 'Stats'):
        self.jsonl_kb += other.jsonl_kb
        self.jsonl_gz_kb += other.jsonl_gz_kb

        self.schema.col_stats.extend(other.schema.col_stats)
        for type_, count in other.schema.nested_type_counts.items():
            self.schema.nested_type_counts[type_] = count + self.schema.nested_type_counts.get(type_, 0)
        for type_, count in other.schema.simple_type_counts.items():
            self.schema.simple_type_counts[type_] = count + self.schema.simple_type_counts.get(type_, 0)

        self.data.row_count += other.data.row_count
        self.data.col_stats.extend(other.data.col_stats)

    def finalize(self):
        self.jsonl_kb = round(self.jsonl_kb, 2)
        self.jsonl_gz_kb = round(self.jsonl_gz_kb, 2)

        self.schema.nested_type_counts = dict(sorted(self.schema.nested_type_counts.items(),
                                                     key=lambda x: x[1], reverse=True))
        self.schema.simple_type_counts = dict(sorted(self.schema.simple_type_counts.items(),
                                                     key=lambda x: x[1], reverse=True))

        return self


def analyse_schema(columns: Schema.ColumnList, parent_stat: SchemaColumnStats = SchemaColumnStats()):
    stats = SchemaStats()
    for col in columns:
        type_ = col.type
        col_stat = SchemaColumnStats(path=parent_stat.path + ("." if parent_stat.path else "") + col.name,
                                     type=type_,
                                     depth=parent_stat.depth + 1,
                                     list_depth=parent_stat.list_depth + (1 if type_ in {'list', 'map'} else 0))
        stats.col_stats.append(col_stat)

        children = col.get_children()
        if children:
            stats.nested_type_counts[type_] = 1 + stats.nested_type_counts.get(type_, 0)

            children_stats = analyse_schema(children, col_stat)
            stats.col_stats.extend(children_stats.col_stats)
            for type_, count in children_stats.nested_type_counts.items():
                stats.nested_type_counts[type_] = count + stats.nested_type_counts.get(type_, 0)
            for type_, count in children_stats.simple_type_counts.items():
                stats.simple_type_counts[type_] = count + stats.simple_type_counts.get(type_, 0)
        else:
            stats.simple_type_counts[type_] = 1 + stats.simple_type_counts.get(type_, 0)
            parent_stat.simple_subfields += 1

    return stats


def find_paths(duckcon: duckdb.DuckDBPyConnection, columns: Schema.ColumnList, path: list[Schema.Column] = None):
    if path is None:
        path = []

    for col in columns:
        col_path = path + [col]
        col_path_str = ''
        parens = 0
        seen_list = False
        for i in range(0, len(col_path)):
            if i > 0 and (col_path[i - 1].type == 'list' or col_path[i - 1].type == 'map'):
                while parens > 0:
                    col_path_str += ')'
                    parens -= 1

                if seen_list:
                    col_path_str = f"flatten({col_path_str})"
                col_path_str = f"list_transform({col_path_str}, l -> l"
                parens = 1
                seen_list = True

            if i == 0 or col_path[i - 1].type != 'list':
                if i > 0:
                    col_path_str += '.'
                col_path_str += '"' + col_path[i].name + '"'

            if col_path[i].type == 'map':
                if seen_list:
                    parts = col_path_str.split('l -> l')
                    last_part = parts[-1]
                    prefix = 'l -> l'.join(parts[:-1])
                    col_path_str = f"{prefix}l -> map_entries(l{last_part})"
                else:
                    col_path_str = f"map_entries({col_path_str})"

        while parens > 0:
            col_path_str += ')'
            parens -= 1

        if seen_list:
            col_path_str = f"unnest({col_path_str})"

        yield col_path_str, col.type

        children = col.get_children()
        if children:
            yield from find_paths(duckcon, children, col_path)


DATASETS = {
    'amazon-berkeley-objects',
    'aws-public-blockchain',
    'clinvar_summary_variants',
    'hep-adl-ethz',
    'gnomad',
    'gtex_8',
    'opentargets_latest',
    'thousandgenomes_dragen',
    'cord-19',
    'daylight-openstreetmap',
    'gharchive',
    'overturemaps',
    'twitter-stream'
}


def analyze_table(table_dir: Path):
    try:
        schema_file = table_dir / 'schema.json'
        with schema_file.open() as f:
            schema = Schema.from_json(json.load(f))

        schema.columns = remove_json_types(schema.columns)
        schema_stats = analyse_schema(schema.columns)

        compressed_data_file = table_dir / 'data.jsonl.gz'
        data_file = compressed_data_file.with_suffix('')
        if not data_file.exists():
            decompress_file(compressed_data_file)
        elif not compressed_data_file.exists():
            compress_file(data_file)

        print(f"Analyzing {table_dir.name}...")
        analysis_dir = create_empty_folder(table_dir / 'analysis')

        duckfile = analysis_dir / 'analyze_duck.db'
        data_stats = DataStats()
        with duckdb.connect(duckfile.as_posix()) as duckcon:
            duckdb_schema = schema.duckdb_schema()
            duckdb_schema_str = {k: v.__str__() for k, v in duckdb_schema.items()}
            duckcon.sql(f"CREATE TABLE data AS "
                        f"SELECT * FROM read_json('{data_file.as_posix()}', columns={duckdb_schema_str})")
            data_stats.row_count = duckcon.sql("SELECT COUNT(*) FROM data").fetchone()[0]

            for col_path, type_ in find_paths(duckcon, schema.columns):
                col_stats = ColumnStats(path=col_path, type=type_)
                data_stats.col_stats.append(col_stats)

                sql = f"SELECT COUNT(*) FROM (SELECT {col_path} FROM data)"
                col_stats.row_count = duckcon.sql(sql).fetchone()[0]

                if col_stats.row_count > 0:
                    sql = f"SELECT COUNT(*) FROM (SELECT {col_path} d FROM data) WHERE d IS NULL"
                    col_stats.null_percentage = 100 * duckcon.sql(sql).fetchone()[0] / col_stats.row_count

                    sql = f"SELECT COUNT(*) FROM (SELECT DISTINCT {col_path} FROM data)"
                    col_stats.unique_percentage = 100 * duckcon.sql(sql).fetchone()[0] / col_stats.row_count

                if type_ in {'varchar', 'list', 'map'}:
                    sql = f"SELECT MIN(l), AVG(l), MAX(l) FROM (SELECT len({col_path}) l FROM data)"
                    col_stats.min_length, col_stats.avg_length, col_stats.max_length = duckcon.sql(sql).fetchone()

                    sql = (f"WITH T AS (SELECT {col_path} s FROM data) "
                           f"SELECT 100 * (SELECT COUNT(*) FROM T WHERE len(s) = 0) / (SELECT COUNT(*) FROM T)")
                    col_stats.empty_percentage = duckcon.sql(sql).fetchone()[0]

                print(f"Handled {table_dir.name} column {col_path}")

        delete_folder(analysis_dir)
        print(f"Finished analyzing {table_dir.name}")

        table_name = table_dir.name
        dataset = ''
        for ds in DATASETS:
            if ds in table_name:
                dataset = ds
                table_name = table_name.split(ds)[-1][1:]
                break

        return Stats(dataset=dataset, name=table_name, jsonl_kb=data_file.stat().st_size / 1024,
                     jsonl_gz_kb=compressed_data_file.stat().st_size / 1024, schema=schema_stats,
                     data=data_stats).finalize()

    except Exception as e:
        print(f"Error analyzing {table_dir.name}: {e}", file=sys.stderr)
        raise e


def main():
    table_stats = []
    with ProcessPoolExecutor(max_workers=PROCESS_POOL_SIZE) as executor:
        futures = [executor.submit(analyze_table, table_dir) for table_dir in TABLES_DIR.iterdir()]
        for future in concurrent.futures.as_completed(futures):
            e = future.exception()
            if e is not None:
                raise e
            table_stats.append(future.result())

            table_stats.sort(key=lambda x: x.dataset + x.name)

            global_stats = Stats(dataset='total', name='total', jsonl_kb=0, jsonl_gz_kb=0,
                                 schema=SchemaStats(), data=DataStats())
            for stats in table_stats:
                global_stats.merge(stats)
            table_stats.append(global_stats.finalize())

            with Path('./analysis/table_stats.json').open('w') as f:
                json.dump(table_stats, f, indent=2, default=lambda x: x.__dict__)

            table_stats.pop()


if __name__ == '__main__':
    main()
