import oci
import logging
import datetime
import argparse

def report_daily_costs(tenant_id, ons_topic_id):
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    time_usage_started = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    time_usage_ended = now.replace(hour=0, minute=0, second=0, microsecond=0)

    one_day_ago_amount = 0
    two_days_ago_amount = 0

    ## Yesterday
    data = usage_api_client.request_summarized_usages(
                request_summarized_usages_details=oci.usage_api.models.RequestSummarizedUsagesDetails(
                    tenant_id=tenant_id,
                    time_usage_started=time_usage_started,
                    time_usage_ended=time_usage_ended,
                    granularity="DAILY"
                )
            ).data
    
    for item in data.items:
        if item.computed_amount is None:
            continue
        
        one_day_ago_amount += item.computed_amount
        currency = item.currency

    ## The day before yesterday
    data = usage_api_client.request_summarized_usages(
                request_summarized_usages_details=oci.usage_api.models.RequestSummarizedUsagesDetails(
                    tenant_id=tenant_id,
                    time_usage_started=time_usage_started - datetime.timedelta(days=1),
                    time_usage_ended=time_usage_ended - datetime.timedelta(days=1),
                    granularity="DAILY"
                )
            ).data
    
    for item in data.items:
        if item.computed_amount is None:
            continue
        
        two_days_ago_amount += item.computed_amount

    difference = (one_day_ago_amount / two_days_ago_amount) * 100 - 100

    # Notification
    title =""
    tenancy = None
    if signer is not None:
        tenancy = identity_client.get_tenancy(signer.tenancy_id).data
    else:
        tenancy = identity_client.get_tenancy(config["tenancy"]).data

    if difference > 0:
        title = "[" + f'{difference:,.2f}' + "% Up]"
    elif difference == 0:
        title = "[No Difference]"
    else:
        title = "[" + f'{difference:,.2f}' + "% Down]"

    title += " Tenancy " + tenancy.name + ": Daily Cost Report (" + time_usage_started.strftime('%m') + "/" + time_usage_started.strftime('%d') + ") - "
    title += currency + " " + f'{one_day_ago_amount:,.0f}'
    title += " (EOM)"

    logging.getLogger().info("ons_topic_id: " + ons_topic_id)

    notification_message = {"title": title, "body": " "}
    logging.getLogger().info("notification_message: " + str(notification_message))
    notification_client.publish_message(ons_topic_id, notification_message)    

def prep_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tenant_id', default='',
                        help='The tenant where you want to get a daily cost report')
    parser.add_argument('--ons_topic_id', default='',
                        help='The notification topic id where you want to publish a message for notifying ')    
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('oci._vendor.urllib3').setLevel(logging.INFO)

    # Starts a timer for the execution time.
    logging.getLogger().info('Report Daily Costs v 0.1')
    start_time = datetime.datetime.now()
    logging.getLogger().info('Script execution start time: {0}'.format(
        start_time.replace(microsecond=0).isoformat()))    

    # Default config file and profile
    #config = oci.config.from_file()
    #signer = None
    #signer = oci.auth.signers.get_resource_principals_signer()

    config = {}
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

    identity_client = oci.identity.IdentityClient(config={}, signer=signer)
    notification_client = oci.ons.NotificationDataPlaneClient(config, signer=signer)
    usage_api_client = oci.usage_api.UsageapiClient(config, signer=signer)

    args = prep_arguments()
    tenant_id = args.tenant_id
    ons_topic_id = args.ons_topic_id

    report_daily_costs(tenant_id, ons_topic_id)
