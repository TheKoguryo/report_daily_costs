#!/bin/bash

###########################################################
# Main
###########################################################
echo "Start running at `date`..."

python3 report_daily_costs.py --tenant_id $TENANT_ID --ons_topic_id $ONS_TOPIC_ID

echo "Completed at `date`.."
