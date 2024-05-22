# RealNest - Nested Data from Real-World Datasets

This repository contains the details of the **RealNest** dataset, a collection of nested data from real-world datasets.
The
dataset is designed to help benchmark and evaluate systems supporting nested data types.

Since some data sources are updated frequently with the most recent data available, the **RealNest** dataset is provided
as a dynamic dataset that can be downloaded via a download script. Please refer to the [README](scripts/README.md) in
the [scripts](scripts) directory for more details.

**RealNest** is also provided as a static dataset downloaded in mid-May 2024 for convenience. The static version of the
dataset comes in two sizes: $64 * 1024$ and $10 * 64 * 1024$ rows, and will soon be available for download.
The [sample-data](sample-data) directory contains a small sample of the dataset (the first 1024 rows of each table) as a
preview.

## Dataset Structure

The dataset contains a directory for each table with the following files:

- `schema.json`: The schema of the table. The schema is a JSON object with a single key `columns`, containing a list of
  columns. Each column is a JSON object with 2 or 3 keys:
    - `name` - The name of the column as a string.
    - `type` - The type of the column as a string.
    - `children` - Optional, only exists for nested types. Describes the child types of the nested type as a list of
      column objects.
- `data.jsonl` or `data.jsonl.gz`: The data of the table in [JSON Lines](https://jsonlines.org/) format (optionally
  Gzip compressed).

The schema might contain a `JSON` type, which may happen for empty JSON objects in the data (`{}`) or when DuckDB's
schema inference detects incompatible types. The columns of this type can be ignored since they are not typical for
structured data, or they can be handled as VARCHAR columns, where the value is the JSON string.
