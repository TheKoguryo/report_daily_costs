#!/bin/bash

export APPDIR=$HOME/report_daily_costs
export TENANT_ID=ocid1.tenancy.oc1..aaaaaaaa.....
export ONS_TOPIC_ID=ocid1.onstopic.oc1.iad.aaaaaaaa.....

cd $APPDIR

###########################################################
# Main
###########################################################
echo "Start running at `date`..."

python3 $APPDIR/report_daily_costs.py -ip --ons_topic_id $ONS_TOPIC_ID

echo "Completed at `date`.."
