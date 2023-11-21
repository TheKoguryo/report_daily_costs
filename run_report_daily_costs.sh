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
# Notify at 23:00 UCT
#
# Check the yesterday's cost every hours that is under being calculated.
* (Your monthly invoice might differ from this estimate. Usage data is typically delayed by approximately twenty four hours.)
# at 23:00 UCT: Notify the yesterday's cost
# at 00:00 UCT ~ 22:00 UCT: If the yesterday's cost is more than the cost of the day before yesterday and the difference is over threshold, notify at that time.
# at 00:00 UCT ~ 22:00 UCT: At the same day, another notification will be occurred when the new difference is over the first notified difference + second threshold(alert_threshold_n)

python3 $APPDIR/report_daily_costs_v2.py -ip --ons_topic_id $ONS_TOPIC_ID --bucket_name $BUCKET_NAME --alert_threshold 30 --alert_threshold_n 20

echo "Completed at `date`.."