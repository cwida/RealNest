# RealNest Sample

Here, you can find a small sample of the **RealNest** dataset. The [1024rows](1024rows) directory contains the first
1024 rows of each table, and the [100mib](100mib) directory contains the largest multiple of 1024 rows such that the
file size is under 100 MiB and the number of rows is less than 64 * 1024 for each table.

The data in this repository is only provided for convenience and to facilitate standardized comparisons. It can be
re-generated from the original sources using the scripts in the [scripts](../scripts) directory. By using the data in
this repository, you agree to the terms of use of the original data sources. The data source for each table is given
below:

| #  | Table / Folder Name                                                   | Data Source                                      |
|----|-----------------------------------------------------------------------|--------------------------------------------------|
| 1  | amazon-berkeley-objects-listings                                      | \[1\] Amazon Berkeley Objects                    |
| 2  | aws-public-blockchain-btc-transactions                                | \[2\] AWS Public Blockchain Data                 |
| 3  | aws-public-blockchain-eth-logs                                        | \[2\] AWS Public Blockchain Data                 |
| 4  | aws-roda-hcls-datalake-clinvar_summary_variants-gene_specific_summary | \[3\] Data Lake as Code                          |
| 5  | aws-roda-hcls-datalake-clinvar_summary_variants-hgvs4variation        | \[3\] Data Lake as Code                          |
| 6  | aws-roda-hcls-datalake-clinvar_summary_variants-submission_summary    | \[3\] Data Lake as Code                          |
| 7  | aws-roda-hcls-datalake-gnomad-sites                                   | \[3\] Data Lake as Code                          |
| 8  | aws-roda-hcls-datalake-gtex_8-rnaseqcv1_1_9_gene_tpm                  | \[3\] Data Lake as Code                          |
| 9  | aws-roda-hcls-datalake-gtex_8-rsemv1_3_0_transcript_expected_count    | \[3\] Data Lake as Code                          |
| 10 | aws-roda-hcls-datalake-gtex_8-rsemv1_3_0_transcript_tpm               | \[3\] Data Lake as Code                          |
| 11 | aws-roda-hcls-datalake-opentargets_latest-aotfelasticsearch           | \[3\] Data Lake as Code                          |
| 12 | aws-roda-hcls-datalake-opentargets_latest-cooccurrences               | \[3\] Data Lake as Code                          |
| 13 | aws-roda-hcls-datalake-opentargets_latest-diseasetophenotype          | \[3\] Data Lake as Code                          |
| 14 | aws-roda-hcls-datalake-opentargets_latest-epmccooccurrences           | \[3\] Data Lake as Code                          |
| 15 | aws-roda-hcls-datalake-opentargets_latest-failedcooccurrences         | \[3\] Data Lake as Code                          |
| 16 | aws-roda-hcls-datalake-opentargets_latest-failedmatches               | \[3\] Data Lake as Code                          |
| 17 | aws-roda-hcls-datalake-opentargets_latest-interaction                 | \[3\] Data Lake as Code                          |
| 18 | aws-roda-hcls-datalake-opentargets_latest-interactionevidence         | \[3\] Data Lake as Code                          |
| 19 | aws-roda-hcls-datalake-opentargets_latest-knowndrugsaggregated        | \[3\] Data Lake as Code                          |
| 20 | aws-roda-hcls-datalake-opentargets_latest-matches                     | \[3\] Data Lake as Code                          |
| 21 | aws-roda-hcls-datalake-thousandgenomes_dragen-var_partby_samples      | \[3\] Data Lake as Code                          |
| 22 | cord-19-document_parses                                               | \[4\] CORD-19                                    |
| 23 | daylight-openstreetmap-osm_elements                                   | \[5\] Daylight Map Distribution of OpenStreetMap |
| 24 | daylight-openstreetmap-osm_features                                   | \[5\] Daylight Map Distribution of OpenStreetMap |
| 25 | gharchive-CommitCommentEvent                                          | \[6\] GitHub Archive                             |
| 26 | gharchive-ForkEvent                                                   | \[6\] GitHub Archive                             |
| 27 | gharchive-GollumEvent                                                 | \[6\] GitHub Archive                             |
| 28 | gharchive-IssueCommentEvent                                           | \[6\] GitHub Archive                             |
| 29 | gharchive-IssuesEvent                                                 | \[6\] GitHub Archive                             |
| 30 | gharchive-MemberEvent                                                 | \[6\] GitHub Archive                             |
| 31 | gharchive-PullRequestEvent                                            | \[6\] GitHub Archive                             |
| 32 | gharchive-PullRequestReviewCommentEvent                               | \[6\] GitHub Archive                             |
| 33 | gharchive-PullRequestReviewEvent                                      | \[6\] GitHub Archive                             |
| 34 | gharchive-PushEvent                                                   | \[6\] GitHub Archive                             |
| 35 | gharchive-ReleaseEvent                                                | \[6\] GitHub Archive                             |
| 36 | hep-adl-ethz-Run2012B_SingleMu                                        | \[7\] CERN Open Data                             |
| 37 | overturemaps-us-west-2-admins                                         | \[8\] Overture Maps Foundation Open Map Data     |
| 38 | overturemaps-us-west-2-base                                           | \[8\] Overture Maps Foundation Open Map Data     |
| 39 | overturemaps-us-west-2-buildings                                      | \[8\] Overture Maps Foundation Open Map Data     |
| 40 | overturemaps-us-west-2-divisions                                      | \[8\] Overture Maps Foundation Open Map Data     |
| 41 | overturemaps-us-west-2-places                                         | \[8\] Overture Maps Foundation Open Map Data     |
| 42 | overturemaps-us-west-2-transportation                                 | \[8\] Overture Maps Foundation Open Map Data     |
| 43 | twitter-stream-2023-01                                                | \[9\] Twitter Stream Archive                     |

Data source numbers refer to [the Attribution section of the main README.md](../README.md#attribution) file.
