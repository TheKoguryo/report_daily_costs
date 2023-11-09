#!/bin/bash

export APPDIR=$HOME/report_daily_costs
export TENANT_ID=ocid1.tenancy.oc1..aaaaaaaa.....
export ONS_TOPIC_ID=ocid1.onstopic.oc1.iad.aaaaaaaa.....
export BUCKET_NAME=daily-costs-bucket

cd $APPDIR

###########################################################
# Main
###########################################################
echo "Start running at `date`..."

# cron schedule - 0 * * * * 
# Notify at 23:00
#
# Check the yesterday's cost every hours that is under being calculated.
# If that cost is more than the cost of the day before yesterday and the difference is over threshold, notify at that time.
python3 $APPDIR/report_daily_costs_v2.py -ip --ons_topic_id $ONS_TOPIC_ID --bucket_name $BUCKET_NAME --alert_threshold 50

echo "Completed at `date`.."
