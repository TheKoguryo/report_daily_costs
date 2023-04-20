# report-daily-costs

## OCI CLI usage-api example

```
oci usage-api usage-summary request-summarized-usages --tenant-id ocid1.tenancy.oc1..aaaaaaaa.....xxxxx --time-usage-started 2023-04-19T06:00 --time-usage-ended 2023-04-19T07:00 --granularity HOURLY

oci usage-api usage-summary request-summarized-usages --tenant-id ocid1.tenancy.oc1..aaaaaaaa.....xxxxx --time-usage-started 2023-04-19T05:00 --time-usage-ended 2023-04-19T06:00 --granularity HOURLY --group-by ["service"]

oci usage-api usage-summary request-summarized-usages --tenant-id ocid1.tenancy.oc1..aaaaaaaa.....xxxxx --time-usage-started 2023-04-19T00:00 --time-usage-ended 2023-04-20T00:00 --granularity DAILY

oci usage-api usage-summary request-summarized-usages --tenant-id ocid1.tenancy.oc1..aaaaaaaa.....xxxxx --time-usage-started 2023-04-19T00:00 --time-usage-ended 2023-04-20T00:00 --granularity DAILY --group-by ["service"]
```
