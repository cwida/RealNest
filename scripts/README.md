# RealNest Dataset Downloader

This script downloads the RealNest dataset - the nested fields of the various Parquet and JSON datasets.

If a table has more rows than requested, only the last `n` rows are downloaded to get the latest data available. Hence,
each run of the script might download different data.

## Requirements

- Python >= 3.9
- Large enough disk space to store the downloaded data. Please note that the dataset is downloaded in parallel, and the
  downloaded data size can be much larger than the compressed size of the dataset.

## Install Dependencies

Install the Python dependencies using the following command:

```bash
pip3 install -r requirements.txt
```

### DuckDB

This script requires Map type inference functionality of DuckDB JSON reader, which is scheduled to be released in DuckDB
v1.1.0. Until then, one can do the following to install DuckDB v0.10.2 with the required feature from the source:

1. Follow [DuckDB Build Prerequisites](https://duckdb.org/docs/dev/building/build_instructions.html#prerequisites) page
   to install the required DuckDB build dependencies.
2. Clone the patched DuckDB repository:
   ```bash
   git clone -b v0.10.2-with-json-map --single-branch https://github.com/ZiyaZa/duckdb.git
   ```
3. If using a Python virtual environment, make sure it is activated.
4. Execute the following command in the root folder of the DuckDB repository to build and install the DuckDB python
   package:
   ```bash
   EXTENSION_STATIC_BUILD=1 GEN=ninja BUILD_PYTHON=1 OVERRIDE_GIT_DESCRIBE=v0.10.2 ENABLE_EXTENSION_AUTOLOADING=1 ENABLE_EXTENSION_AUTOINSTALL=1 make
   ```

## Configuration

Look at the comments in the [config.py](config.py) file to see the available configuration options and modify them as
needed. The options can be overridden by setting the corresponding environment variables.

## Download Dataset

Run the [download.py](download.py) script to download the RealNest dataset:

```bash
python3 download.py
```
