# RealNest - Nested Data from Real-World Datasets

This repository contains the details of the **RealNest** dataset, a collection of nested data from real-world datasets.
The
dataset is designed to help benchmark and evaluate systems supporting nested data types.

Since some data sources are updated frequently with the most recent data available, the **RealNest** dataset is provided
as a dynamic dataset that can be downloaded via a download script. Please refer to the [README](scripts/README.md) in
the [scripts](scripts) directory for more details.

**RealNest** is also provided as a static dataset downloaded in mid-May 2024 for convenience. The static version of the
dataset comes in two sizes: 64 * 1024 and 10 * 64 * 1024 rows, and will soon be available for download.
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

## License

The data has been downloaded from various public sources and converted to a common format. By using the **RealNest**
dataset, you agree to the terms of use of the original data sources. The dataset is safe to use for research purposes
only. If you are unsure about the terms, please refer to the licenses of the original data sources. The sources are:

- Open Data on AWS entries listed [here](scripts/parquet_metadata.json)
    - [Daylight Map Distribution of OpenStreetMap](https://registry.opendata.aws/daylight-osm/) ([Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/1-0/))
    - [Overture Maps Foundation Open Map Data](https://registry.opendata.aws/overture/)
        - Overture data is licensed under the Community Database License Agreement Permissive v2 (CDLA) unless derived
          from a source that requires publishing under a different license, such as data derived from OpenStreetMap,
          that constitutes a 'Derivative Database' (as defined under ODbL v1.0), which will be licensed under ODbL v1.0.
    - [AWS Public Blockchain Data](https://registry.opendata.aws/aws-public-blockchain/) ([LICENSE](https://github.com/aws-solutions-library-samples/guidance-for-digital-assets-on-aws/blob/main/LICENSE))
    - [Data Lake as Code](https://github.com/aws-samples/data-lake-as-code) ([ATTRIBUTIONS](https://github.com/aws-samples/data-lake-as-code/blob/roda/docs/roda_attributions.txt))
- [CERN Open Data](https://opendata.cern.ch/record/6021)
    - CMS collaboration (2017). SingleMu primary dataset in AOD format from Run of 2012 (
      /SingleMu/Run2012B-22Jan2013-v1/AOD). CERN Open Data Portal.
      DOI:[10.7483/OPENDATA.CMS.IYVQ.1J0W](http://doi.org/10.7483/OPENDATA.CMS.IYVQ.1J0W)
- [Amazon Berkeley Objects Listings](https://amazon-berkeley-objects.s3.us-east-1.amazonaws.com/index.html) ([LICENSE](https://amazon-berkeley-objects.s3.us-east-1.amazonaws.com/LICENSE-CC-BY-4.0.txt))
    - J. Collins, S. Goel, K. Deng, A. Luthra, L. Xu, E. Gundogdu, X. Zhang, T. F. Yago
      Vicente, T. Dideriksen, H. Arora, M. Guillaumin, and J. Malik, "Abo: Dataset and
      benchmarks for real-world 3d object understanding," CVPR, 2022.
- [GitHub Archive](https://www.gharchive.org/)
- [Twitter Stream Archive](https://archive.org/details/twitterstream)
- [CORD-19](https://allenai.org/data/cord-19) ([LICENSE](https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/2020-03-13/COVID.DATA.LIC.AGMT.pdf))
    - L. L. Wang, K. Lo, Y. Chandrasekhar, R. Reas, J. Yang, D. Eide, K. Funk, R. M.
      Kinney, Z. Liu, W. Merrill, P. Mooney, D. A. Murdick, D. Rishi, J. Sheehan, Z. Shen,
      B. Stilson, A. D. Wade, K. Wang, C. Wilhelm, B. Xie, D. A. Raymond, D. S. Weld,
      O. Etzioni, and S. Kohlmeier, "Cord-19: The covid-19 open research dataset," ArXiv, 2020.

In addition, the dataset is licensed under the [MIT License](LICENSE).
