#!/usr/bin/env python3
# @author: TheKoguryo

import oci
import logging
import datetime
import argparse

version = "23.05.04"

def report_daily_costs_with_forecast(tenant_id, ons_topic_id):
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - datetime.timedelta(days=1)
    two_days_ago = today - datetime.timedelta(days=2)
    tomorrow = today + datetime.timedelta(days=1)

    one_day_ago_amount = 0
    two_days_ago_amount = 0
    one_day_ago_forecast_amount = 0
    today_ago_forecast_amount = 0

    title = ""
    body = ""

    ## Yesterday
    data = usage_api_client.request_summarized_usages(
                request_summarized_usages_details=oci.usage_api.models.RequestSummarizedUsagesDetails(
                    tenant_id=tenant_id,
                    time_usage_started=yesterday,
                    time_usage_ended=today,
                    granularity="DAILY"
                )
            ).data
    
    print("data: " + str(data))

    for item in data.items:
        if item.computed_amount is None or item.computed_amount == 0.0:
            continue
        
        one_day_ago_amount += item.computed_amount
        currency = item.currency

        body = "(" + item.time_usage_started.strftime('%m') + "/" + item.time_usage_started.strftime('%d') + ") " + f'{item.computed_amount:,.0f}' + "\n"

    # Forecast
    data = usage_api_client.request_summarized_usages(
                request_summarized_usages_details=oci.usage_api.models.RequestSummarizedUsagesDetails(
                    tenant_id=tenant_id,
                    time_usage_started=two_days_ago,
                    time_usage_ended=yesterday,
                    granularity="DAILY",
                    forecast=oci.usage_api.models.Forecast(
                        time_forecast_started=yesterday,
                        time_forecast_ended=tomorrow,
                        forecast_type="BASIC"
                    )
                )
            ).data
    
    for item in data.items:
        if item.computed_amount is None or item.computed_amount == 0.0:
            continue

        if item.is_forecast == True:
            message = "(" + item.time_usage_started.strftime('%m') + "/" + item.time_usage_started.strftime('%d') + ") " + f'{item.computed_amount:,.0f}' + " (forecasted)\n"
        else:
            message = "(" + item.time_usage_started.strftime('%m') + "/" + item.time_usage_started.strftime('%d') + ") " + f'{item.computed_amount:,.0f}' + "\n"

        if item.time_usage_started.strftime('%y-%m-%d') == two_days_ago.strftime('%y-%m-%d'):
            print("item: " + str(item))
            two_days_ago_amount += item.computed_amount
            body = message + body

        if item.time_usage_started.strftime('%y-%m-%d') == yesterday.strftime('%y-%m-%d'):
            print("item: " + str(item))
            one_day_ago_forecast_amount += item.computed_amount
            body += message

        if item.time_usage_started.strftime('%y-%m-%d') == today.strftime('%y-%m-%d'):
            print("item: " + str(item))
            today_ago_forecast_amount += item.computed_amount
            body += message

    difference = (one_day_ago_amount / two_days_ago_amount) * 100 - 100

    # Notification
    tenancy = identity_client.get_tenancy(tenant_id).data

    if difference > 0:
        title = "[" + f'{difference:,.2f}' + "% ⬆]"
    elif difference == 0:
        title = "[No Difference]"
    else:
        title = "[" + f'{difference:,.2f}' + "% ⬇]"

    title += " Tenancy " + tenancy.name + ": Daily Cost Report (" + yesterday.strftime('%m') + "/" + yesterday.strftime('%d') + " UTC) - "
    title += currency + " " + f'{one_day_ago_amount:,.0f}'
    title += " (EOM)"

    if difference > alert_threshold or datetime.datetime.now().hour == 23 :
        logging.getLogger().info("ons_topic_id: " + ons_topic_id)
    
        notification_message = {"title": title, "body": body}
        logging.getLogger().info("notification_message: " + str(notification_message))
        notification_client.publish_message(ons_topic_id, notification_message)    


def prep_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tenant_id', default='', dest='tenant_id',
                        help='The tenant where you want to get a daily cost report')
    parser.add_argument('--ons_topic_id', default='', dest='ons_topic_id',
                        help='The notification topic id where you want to publish a message for notifying ')
    parser.add_argument('--alert_threshold', default='', dest='alert_threshold',
                        help='The threshold which you want to notify it over than ')    
    parser.add_argument('-ip', action='store_true', default=False,
                        help='Use Instance Principals for Authentication')
    
    args = parser.parse_args()

    if not (args.ip) and not (args.tenant_id):
        print("You must specify tenant_id!!")

        return None
        
    return args

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('oci._vendor.urllib3').setLevel(logging.INFO)

    # Starts a timer for the execution time.
    logging.getLogger().info('Report Daily Costs v{0}'.format(version))
    start_time = datetime.datetime.now()
    logging.getLogger().info('Script execution start time: {0}'.format(
        start_time.replace(microsecond=0).isoformat()))    

    args = prep_arguments()

    if args is None:
        exit()    

    if args.ip == True:
        config = {}
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

        tenant_id = signer.tenancy_id

        identity_client = oci.identity.IdentityClient(config=config, signer=signer)
        notification_client = oci.ons.NotificationDataPlaneClient(config=config, signer=signer)
        usage_api_client = oci.usage_api.UsageapiClient(config=config, signer=signer)
    else:
        config = oci.config.from_file()
        signer = None

        tenant_id = args.tenant_id

        identity_client = oci.identity.IdentityClient(config=config)
        notification_client = oci.ons.NotificationDataPlaneClient(config=config)
        usage_api_client = oci.usage_api.UsageapiClient(config=config)

    ons_topic_id = args.ons_topic_id
    alert_threshold = args.alert_threshold

    report_daily_costs_with_forecast(tenant_id, ons_topic_id, alert_threshold)
