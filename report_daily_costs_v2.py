#!/usr/bin/env python3
# @author: TheKoguryo

import oci
import logging
import datetime
import argparse
from pytz import reference
import requests

version = "23.11.09"

# Global Variables
identity_client = None
notification_client = None
usage_api_client = None
object_storage_client = None

d_day_total_amount = None
d_day_minus_one_total_amount = None
currency = None

d_day_costs_for_report = None
d_day_service_cost_sum = None
d_day_service_region_cost_sum = None
d_day_minus_one_service_cost_sum = None
d_day_minus_one_service_region_cost_sum = None

sku_list = None


def report_daily_costs_with_forecast(tenant_id, ons_topic_id, alert_threshold, bucket_name):
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    d_day_started = today - datetime.timedelta(days=1)
    d_day_ended = d_day_started + datetime.timedelta(days=1)
    d_day_minus_one_started = today - datetime.timedelta(days=2)

    # global parameters
    global d_day_total_amount
    global d_day_minus_one_total_amount
    global currency
    global d_day_costs_for_report
    global d_day_service_cost_sum
    global d_day_service_region_cost_sum
    global d_day_minus_one_service_cost_sum
    global d_day_minus_one_service_region_cost_sum

    ## SKU
    gather_sku_info()

    ## D-Day : Yesterday
    data = usage_api_client.request_summarized_usages(
                request_summarized_usages_details=oci.usage_api.models.RequestSummarizedUsagesDetails(
                    tenant_id=tenant_id,
                    time_usage_started=d_day_started,
                    time_usage_ended=d_day_ended,
                    granularity="DAILY",
                    group_by=["service", "region", "skuName", "skuPartNumber"]
                )
            ).data
    
    logging.debug("data: " + str(data))

    costs = []
    d_day_total_amount = 0
    d_day_service_cost_sum = dict()
    d_day_service_region_cost_sum = dict()       
    for item in data.items:
        if item.computed_amount is None or item.computed_amount == 0.0:
            continue 

        #if item.service != 'Data Labeling Service - Annotations':
        #    continue

        # Exception Handle
        item.service = item.service.replace("(WAF)", "")

        currency = item.currency
        d_day_total_amount += item.computed_amount  

        if item.service in d_day_service_cost_sum:
            d_day_service_cost_sum[item.service] += item.computed_amount
        else:
            d_day_service_cost_sum[item.service] = item.computed_amount

        if item.service in d_day_service_region_cost_sum:
            if item.region in d_day_service_region_cost_sum[item.service]:
                d_day_service_region_cost_sum[item.service][item.region] += item.computed_amount
            else:
                d_day_service_region_cost_sum[item.service][item.region] = item.computed_amount
        else:
            d_day_service_region_cost_sum[item.service] = dict()
            d_day_service_region_cost_sum[item.service][item.region] = item.computed_amount      
            
        row = { 'service': str(item.service), 'region': str(item.region), 'sku_name': str(item.sku_name), 'sku_part_number': str(item.sku_part_number), 'quantity': item.computed_quantity, 'amount': item.computed_amount }

        costs.append(row)

    # sort by service
    d_day_costs = sorted(costs, key=lambda k: (k['service'], k['region'], k['sku_name'], k['sku_part_number']))

    for row in d_day_costs:
        logging.debug("AFTER SORTED: " + str(row))

    logging.debug("d_day_service_cost_sum: " + str(d_day_service_cost_sum))
    logging.debug("d_day_service_region_cost_sum: " + str(d_day_service_region_cost_sum))            

    ## D-Day Minus One : The Day Before Yesterday
    data = usage_api_client.request_summarized_usages(
                request_summarized_usages_details=oci.usage_api.models.RequestSummarizedUsagesDetails(
                    tenant_id=tenant_id,
                    time_usage_started=d_day_minus_one_started,
                    time_usage_ended=d_day_started,
                    granularity="DAILY",
                    group_by=["service", "region", "skuName", "skuPartNumber"]
                )
            ).data
    
    logging.debug("data: " + str(data))

    costs = []
    d_day_minus_one_total_amount = 0    
    d_day_minus_one_service_cost_sum = dict()
    d_day_minus_one_service_region_cost_sum = dict()
    for item in data.items:
        if item.computed_amount is None or item.computed_amount == 0.0:
            continue  

        #if item.service != 'Data Labeling Service - Annotations':
        #    continue

        # Exception Handle
        item.service = item.service.replace("(WAF)", "")             

        d_day_minus_one_total_amount += item.computed_amount
        currency = item.currency

        if item.service in d_day_minus_one_service_cost_sum:
            d_day_minus_one_service_cost_sum[item.service] += item.computed_amount
        else:
            d_day_minus_one_service_cost_sum[item.service] = item.computed_amount

        if item.service in d_day_minus_one_service_region_cost_sum:
            if item.region in d_day_minus_one_service_region_cost_sum[item.service]:
                d_day_minus_one_service_region_cost_sum[item.service][item.region] += item.computed_amount
            else:
                d_day_minus_one_service_region_cost_sum[item.service][item.region] = item.computed_amount
        else:
            d_day_minus_one_service_region_cost_sum[item.service] = dict()
            d_day_minus_one_service_region_cost_sum[item.service][item.region] = item.computed_amount

        row = { 'service': str(item.service), 'region': str(item.region), 'sku_name': str(item.sku_name), 'sku_part_number': str(item.sku_part_number), 'quantity': item.computed_quantity, 'amount': item.computed_amount }

        costs.append(row)
        logging.debug("d_day_minus_one: " + str(row))

    # sort by service
    d_day_minus_one_costs = sorted(costs, key=lambda k: (k['service'], k['region'], k['sku_name'], k['sku_part_number']))
    for row in d_day_minus_one_costs:
        logging.debug("BEFORE SORTED: " + str(row))

    logging.debug("d_day_minus_one_service_cost_sum: " + str(d_day_minus_one_service_cost_sum))
    logging.debug("d_day_minus_one_service_region_cost_sum: " + str(d_day_minus_one_service_region_cost_sum))            


    # sku_part_number이 같지만, sku_name이 다른 것도 있음에 주의
    # 'sku_name': 'Oracle Autonomous Database Storage', 'sku_part_number': 'B95754'
    # 'sku_name': 'Oracle Autonomous Database Backup Storage', 'sku_part_number': 'B95754'
    ## Difference
    before_index = 0
    d_day_costs_for_report = []

    for after in d_day_costs:
        if before_index >= len(d_day_minus_one_costs):
            quantity_str = get_formatted_float_str(after['quantity'])
            amount_str = get_formatted_float_str(after['amount'])
            difference_str, info, color = get_difference_float_str(0, after['amount'])
            status = info   

            row = { 'service': str(after['service']), 'region': str(after['region']), 'sku_name': str(after['sku_name']), 'sku_part_number': str(after['sku_part_number']), 'quantity': quantity_str, 'amount': amount_str, 'difference': difference_str, 'status': status, 'color': color }

            d_day_costs_for_report.append(row)
            continue

        match = False
        logging.debug("after: " + str(after))

        while match == False and before_index < len(d_day_minus_one_costs):
            before = d_day_minus_one_costs[before_index]
            logging.debug("before: " + str(before))
            logging.debug("before_index: " + str(before_index))

            ## service
            if after['service'] == before['service']:
                logging.debug("after['service'] == before['service']")

                ## region
                if after['region'] == before['region']:

                    ## sku_name
                    if after['sku_name'] == before['sku_name']:

                        ## sku_part_number
                        if after['sku_part_number'] == before['sku_part_number']:
                            logging.debug("match")
                            match = True
                            before_index = before_index + 1
                            break;
                        elif after['sku_part_number'] > before['sku_part_number']:
                            logging.debug("after['sku_part_number'] > before['sku_part_number']")
                            before_index = before_index + 1

                            status = "A"
                            row = { 'service': str(before['service']), 'region': str(before['region']), 'sku_name': str(before['sku_name']), 'sku_part_number': str(before['sku_part_number']), 'quantity': str(before['quantity']), 'amount': str(before['amount']), 'difference': '', 'status': status, 'color': color }
                            d_day_costs_for_report.append(row)
                        else:
                            logging.debug("after['sku_part_number'] < before['sku_part_number']")
                            break                        

                    elif after['sku_name'] > before['sku_name']:
                        logging.debug("after['sku_name'] > before['sku_name']")
                        before_index = before_index + 1

                        difference_str, info, color = get_difference_float_str(before['amount'], 0)
                        status = info  
                        row = { 'service': str(before['service']), 'region': str(before['region']), 'sku_name': str(before['sku_name']), 'sku_part_number': str(before['sku_part_number']), 'quantity': '', 'amount': '', 'difference': difference_str, 'status': status, 'color': color }
                        d_day_costs_for_report.append(row)                       
                    else:
                        logging.debug("after['sku_name'] < before['sku_name']")
                        break

                elif after['region'] > before['region']:
                    logging.debug("after['region'] > before['region']")
                    before_index = before_index + 1

                    difference_str, info, color = get_difference_float_str(before['amount'], 0)
                    status = info  
                    row = { 'service': str(before['service']), 'region': str(before['region']), 'sku_name': str(before['sku_name']), 'sku_part_number': str(before['sku_part_number']), 'quantity': '', 'amount': '', 'difference': difference_str, 'status': status, 'color': color }
                    d_day_costs_for_report.append(row)                    
                else:
                    logging.debug("after['region'] < before['region']")
                    break;
            elif after['service'] > before['service']:
                logging.debug("after['service'] > before['service']")
                before_index = before_index + 1

                difference_str, info, color = get_difference_float_str(before['amount'], 0)
                status = info  
                row = { 'service': str(before['service']), 'region': str(before['region']), 'sku_name': str(before['sku_name']), 'sku_part_number': str(before['sku_part_number']), 'quantity': '', 'amount': '', 'difference': difference_str, 'status': status, 'color': color }
                d_day_costs_for_report.append(row)                   
            else:
                logging.debug("else")
                break;

        if match == True:
            quantity_str = get_formatted_float_str(after['quantity'])
            amount_str = get_formatted_float_str(after['amount'])
            difference_str, info, color = get_difference_float_str(before['amount'], after['amount'])
            status = info  

            row = { 'service': str(after['service']), 'region': str(after['region']), 'sku_name': str(after['sku_name']), 'sku_part_number': str(after['sku_part_number']), 'quantity': quantity_str, 'amount': amount_str, 'difference': difference_str, 'status': status, 'color': color }

            d_day_costs_for_report.append(row)
        else:
            # Not Match
            quantity_str = get_formatted_float_str(after['quantity'])
            amount_str = get_formatted_float_str(after['amount'])
            difference_str, info, color = get_difference_float_str(0, after['amount'])
            status = info              

            row = { 'service': str(after['service']), 'region': str(after['region']), 'sku_name': str(after['sku_name']), 'sku_part_number': str(after['sku_part_number']), 'quantity': quantity_str, 'amount': amount_str, 'difference': difference_str, 'status': status, 'color': color }

            d_day_costs_for_report.append(row)

    # Generate HTML Report and Upload to Object Storage
    report_name = "daily-costs-report-" + d_day_started.strftime("%Y-%m-%d")
    body_html = generate_report(tenant_id, d_day_started)
    report_url = create_report_url(report_name, body_html, bucket_name)

    # Notify
    difference_percent = 0
    if d_day_minus_one_total_amount != 0:
        difference_percent = (d_day_total_amount / d_day_minus_one_total_amount) * 100 - 100

    if difference_percent > 0:
        notification_title = "[" + f'{difference_percent:,.2f}' + "% ⬆]"
    elif difference_percent == 0:
        notification_title = "[No Difference]"
    else:
        notification_title = "[" + f'{difference_percent:,.2f}' + "% ⬇]"

    tenant_name = identity_client.get_tenancy(tenant_id).data.name
    localtime = reference.LocalTimezone()

    notification_title += " Tenancy " + tenant_name + ": Daily Cost Report (" + d_day_started.strftime("%m/%d") + " " + localtime.tzname(d_day_started) + ") - "
    notification_title += currency + " " + f'{d_day_total_amount:,.0f}'
    
    notification_body = "OCI Daily Costs Report for " + tenant_name + " - 집계시간: " + start_time.strftime("%Y-%m-%d %H:%M:%S") + " (" + localtime.tzname(d_day_started) + ")\n"
    notification_body += "- " + d_day_minus_one_started.strftime("%m/%d") + ": " + currency + " " + f'{d_day_minus_one_total_amount:,.0f}' + "\n"
    notification_body += "- " + d_day_started.strftime("%m/%d") + ": " + currency + " " + f'{d_day_total_amount:,.0f}' + " (calculation in progress...) "

    if difference_percent > 0:
        notification_body += "[" + f'{difference_percent:,.2f}' + "% ⬆]"
    elif difference_percent == 0:
        pass
    else:
        notification_body += "[" + f'{difference_percent:,.2f}' + "% ⬇]"

    notification_body += "\n\n\n"    
    notification_body += "Go To the detailed report: "
    notification_body += " -> " + report_url + "\n"

    notification_body += "\n\nYour monthly invoice might differ from this estimate. Usage data is typically delayed by approximately twenty four hours."

    if difference_percent > alert_threshold or datetime.datetime.now().hour == 23 :
        logging.info("ons_topic_id: " + ons_topic_id)
    
        notification_message = {"title": notification_title, "body": notification_body}
        logging.info("notification_message: " + str(notification_message))

        notification_client.publish_message(ons_topic_id, notification_message)


def generate_report(tenant_id, d_day_started):
    localtime = reference.LocalTimezone()

    logging.info("d_day_started:" + d_day_started.strftime("%Y-%m-%d (") + localtime.tzname(d_day_started) + ")")

    tenant_name = identity_client.get_tenancy(tenant_id).data.name

    get_formatted_float_str(d_day_total_amount-d_day_minus_one_total_amount)
    difference_str, info, color = get_difference_float_str(d_day_minus_one_total_amount, d_day_total_amount)

    html = ""
    html += "<!DOCTYPE html>\n"
    html += "<html lang='en'>\n"
    html += "<head>\n"
    html += "	<meta charset='UTF-8'>\n"
    html += "	<title>OCI Daily Costs Report</title>\n"
    html += "	<link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.7/css/bootstrap.min.css'>\n"
    html += "	<style>\n"
    html += "		body {\n"
    html += "			padding-top: 50px;\n"
    html += "			background-color: #33553C;\n"
    html += "		}\n"
    html += "		.hiddenRow {\n"
    html += "			padding: 0 !important;\n"
    html += "		}\n"
    html += "		.table {\n"
    html += "			margin-bottom: 0px;\n"
    html += "		}\n"
    html += "	</style>\n"
    html += "	<script>\n"
    html += "		window.console = window.console || function (t) { };\n"
    html += "	</script>\n"
    html += "</head>\n"
    html += "<body translate='no'>\n"
    html += "	<div class='container'>\n"
    html += "		<div class='col-md-12'>\n"
    html += "			<div class='panel panel-default'>\n"
    html += "				<div class='panel-heading'>OCI Daily Costs Report for <font style='font-weight: bold;'>" + tenant_name + "</font> - 집계시간: " + start_time.strftime("%Y-%m-%d %H:%M:%S") + " (" + localtime.tzname(d_day_started) + ") </div>\n"
    html += "				<div class='panel-body'>\n"
    html += "					<table class='table table-condensed table-striped'>\n"
    html += "						<tbody>\n"
    html += "							<tr style='background-color: white;'>\n"
    html += "								<td colspan='5' style='text-align: center;border-top: 0px'> <font style='font-size: xx-large;'>" + d_day_started.strftime("%Y-%m-%d") + " (" + localtime.tzname(d_day_started) + ")" + "</td>\n"
    html += "								<td colspan='7' width='60%' style='text-align: center;border-top: 0px'> <font style='font-size: xx-large;'>" + currency + " " + get_formatted_float_str(d_day_total_amount)  + "</font> (전일대비: " + currency + " <font style='color: " + color + ";'>" + difference_str + " (" + info + ")" + "</font> )</td>\n"
    html += "							</tr>\n"
    html += "						</tbody>\n"
    html += "				    </table>\n"    
    html += "					<table class='table table-condensed table-striped'>\n"
    html += "						<thead>\n"
    html += "							<tr>\n"
    html += "								<th width='10%'></th>\n"
    html += "								<th colspan='7'>Description</th>\n"
    html += "								<th width='15%' style='text-align: right;'>Usage Quantity</th>\n"
    html += "								<th width='15%' style='text-align: right;'>Amount in KRW</th>\n"
    html += "								<th width='15%' style='text-align: right;'>Difference in KRW</th>\n"
    html += "								<th width='10%' style='text-align: right;'>Info</th>\n"
    html += "							</tr>\n"
    html += "						</thead>\n"
    html += "						<tbody>\n"

    prev_service = ""
    prev_region = ""
    prev_sku_name = ""    
    #pre_sku_part_number = ""
    count = 0
    for row in d_day_costs_for_report:
        if prev_service != row['service']:

            # Service End Tag
            if prev_service != "":

                # Region End Tag
                if prev_region != "":
                    html += "																</tbody>\n"
                    html += "															</table>\n"
                    html += "														</div>\n"
                    html += "													</td>\n"
                    html += "												</tr>\n"
                    html += "												<!-- Region End -->\n"

                html += "											</tbody>\n"
                html += "										</table>\n"
                html += "									</div>\n"
                html += "								</td>\n"
                html += "							</tr>\n"
                html += "							<!-- Service End -->\n"

            # Service Start Tag
            d_day_service_total_cost = 0

            if row['service'] in d_day_service_cost_sum:
                # Exist
                d_day_service_total_cost = d_day_service_cost_sum[row['service']]

            d_day_minus_one_service_total_cost = 0

            if row['service'] in d_day_minus_one_service_cost_sum:
                # Exist
                d_day_minus_one_service_total_cost = d_day_minus_one_service_cost_sum[row['service']]
            
            d_day_service_total_cost_str = get_formatted_float_str(d_day_service_total_cost)
            difference_str, info, color = get_difference_float_str(d_day_minus_one_service_total_cost, d_day_service_total_cost)

            html += "							<!-- Service Start -->\n"
            html += "							<tr data-toggle='collapse' data-target='#" + row['service'].replace(" ","").lower() + "' class='accordion-toggle'>\n"
            html += "								<td colspan='9'><button class='btn btn-default btn-xs'><span class='glyphicon glyphicon-plus'></span></button> " + row['service'] + "</td>\n"
            html += "								<td width='15%' align='right'>" + d_day_service_total_cost_str + "</td>\n"
            html += "								<td width='15%' align='right' style='color: " + color + ";'>" + difference_str + "</td>\n"
            html += "								<td width='10%' align='right' style='color: " + color + ";'>" + info + "</td>\n"
            html += "							</tr>\n"
            html += "							<tr>\n"
            html += "								<td colspan='12' class='hiddenRow'>\n"
            html += "									<div class='accordian-body collapse' id='" + row['service'].replace(" ","").lower() + "'>\n"
            html += "										<table class='table table-condensed table-striped'>\n"
            html += "											<tbody>\n"

        if prev_region != row['region'] or prev_service != row['service']:

            # Region End Tag
            if prev_service == row['service'] and prev_region != "":
                html += "																</tbody>\n"
                html += "															</table>\n"
                html += "														</div>\n"
                html += "													</td>\n"
                html += "												</tr>\n"
                html += "												<!-- Region End -->\n"
            
            # Region Start Tag
            d_day_service_region_total_cost = 0

            if row['service'] in d_day_service_region_cost_sum:
                # Exist
                if row['region'] in d_day_service_region_cost_sum[row['service']]:
                    # Exist
                    d_day_service_region_total_cost = d_day_service_region_cost_sum[row['service']][row['region']]

            d_day_minus_one_service_region_total_cost = 0

            if row['service'] in d_day_minus_one_service_region_cost_sum:
                # Exist
                if row['region'] in d_day_minus_one_service_region_cost_sum[row['service']]:
                    # Exist
                    d_day_minus_one_service_region_total_cost = d_day_minus_one_service_region_cost_sum[row['service']][row['region']]

            d_day_service_region_total_cost_str = get_formatted_float_str(d_day_service_region_total_cost)
            difference_str, info, color = get_difference_float_str(d_day_minus_one_service_region_total_cost, d_day_service_region_total_cost)                    

            html += "												<!-- Region Start -->\n"
            html += "												<tr data-toggle='collapse' class='accordion-toggle' data-target='#" + row['service'].replace(" ","").lower() + "_" + row['region'].replace(" ","").lower() + "'>\n"
            html += "													<td colspan='9'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<button class='btn btn-default btn-xs'><span class='glyphicon glyphicon-plus'></span></button> " + row['region'] + "</td>\n"
            html += "													<td width='15%' align='right'>" + d_day_service_region_total_cost_str + "</td>\n"
            html += "													<td width='15%' align='right' style='color: " + color + ";'>" + difference_str + "</td>\n"
            html += "													<td width='10%' align='right' style='color: " + color + ";'>" + info + "</td>\n"
            html += "												</tr>\n"
            html += "												<tr>\n"
            html += "													<td colspan='12' class='hiddenRow'>\n"
            html += "														<div class='accordian-body collapse' id='" + row['service'].replace(" ","").lower() + "_" + row['region'].replace(" ","").lower() + "'>\n"
            html += "															<table class='table table-condensed table-striped'>\n"
            html += "																<tbody>\n"


        if prev_sku_name != row['sku_name'] or prev_region != row['region'] or prev_service != row['service']:

            # SKU End Tag
            #if pre_sku_part_number != "":

            # SKU Start Tag

            html += "																	<!-- SKU Start -->\n"
            html += "																	<tr data-toggle='collapse' class='accordion-toggle' data-target='#" + row['service'].replace(" ","").lower() + "_" + row['region'].replace(" ","").lower() + "_" + row['sku_name'].replace(" ","").lower() + "'>\n"
            html += "																		<td colspan='12'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<button class='btn btn-default btn-xs'><span class='glyphicon glyphicon-plus'></span></button> " + row['sku_name'] + " ( " + row['sku_part_number'] + " )</td>\n"
            html += "																	</tr>\n"
            html += "																	<tr>\n"
            html += "																		<td colspan='12' class='hiddenRow'>\n"
            #html += "																			<div class='accordian-body collapse' id='" + row['service'].replace(" ","").lower() + "_" + row['region'].replace(" ","").lower() + "_" + row['sku_name'].replace(" ","").lower() + "'>\n"
            html += "																			<div class='accordian-body' id='" + row['service'].replace(" ","").lower() + "_" + row['region'].replace(" ","").lower() + "_" + row['sku_name'].replace(" ","").lower() + "'>\n"
            html += "																				<table class='table table-condensed table-striped'>\n"
            html += "																					<tbody>\n"
            html += "																						<tr style='background-color: white;'>\n"
            #html += " 																							<td colspan='8'></td>\n"
            html += " 																							<td colspan='8'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" + get_sku_part_metricName(row['sku_part_number']) + "</td>\n"            
            html += " 																							<td width='15%' align='right'>" + str(row['quantity']) + "</td>\n"
            html += " 																							<td width='15%' align='right'>" + str(row['amount']) + "</td>\n"
            html += " 																							<td width='15%' align='right' style='color: " + row['color'] + ";'>" + str(row['difference']) + "</td>\n"
            html += " 																							<td width='10%' align='right' style='color: " + row['color'] + ";'>" + str(row['status']) + "</td>\n"
            html += "																						</tr>\n"
            html += "																					</tbody>\n"
            html += "																				</table>\n"
            html += "																			</div>\n"
            html += "																		</td>\n"
            html += "																	</tr>\n"

        prev_service = row['service']
        prev_region = row['region']
        prev_sku_name = row['sku_name']

    # Region End Tag
    if prev_region != "":
        html += "																</tbody>\n"
        html += "															</table>\n"
        html += "														</div>\n"
        html += "													</td>\n"
        html += "												</tr>\n"
        html += "												<!-- Region End -->\n"

    # Service End Tag
    if prev_service != "":
        html += "											</tbody>\n"
        html += "										</table>\n"
        html += "									</div>\n"
        html += "								</td>\n"
        html += "							</tr>\n"
        html += "							<!-- Service End -->\n"

    html += "						</tbody>\n"
    html += "					</table>\n"
    html += "				</div>\n"
    html += "			</div>\n"
    html += "		</div>\n"
    html += "	</div>\n"
    html += "	<script src='https://cdnjs.cloudflare.com/ajax/libs/jquery/3.1.0/jquery.min.js'></script>\n"
    html += "	<script src='https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.7/js/bootstrap.min.js'></script>\n"
    html += "</body>\n"
    html += "</html>\n" 

    logging.debug(html)

    return html

def create_report_url(name, body_html, bucket_name):
    namespace_name = object_storage_client.get_namespace(retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY).data
    object_name = name + ".html"
    #body_html = "<html><body><h1>hello</h1></body></html>"

    object_storage_client.put_object(namespace_name, bucket_name, object_name, body_html.encode('utf-8'), content_type="text/html")

    par_time_expires = datetime.datetime.now() + datetime.timedelta(days=1)
    #par_name = "daily-costs-bucket-" + d_day_started.strftime("%Y-%m-%d")
    par_name = "par for " + name + ".html"

    create_preauthenticated_request_response = object_storage_client.create_preauthenticated_request(
        namespace_name=namespace_name,
        bucket_name=bucket_name,
        create_preauthenticated_request_details=oci.object_storage.models.CreatePreauthenticatedRequestDetails(
            name=par_name,
            access_type="ObjectRead",
            time_expires=par_time_expires,
            bucket_listing_action="ListObjects",
            object_name=object_name)
        )

    region = config['region']
    object_par_url = "https://" + namespace_name + ".objectstorage." + region + ".oci.customer-oci.com"  + create_preauthenticated_request_response.data.access_uri

    logging.info(object_par_url)

    return object_par_url

def get_sku_part_metricName(part_number):
    metric_name = ''

    try:
        metric_name = sku_list[part_number]
    except KeyError:
        logging.debug("Key Not Found - " + part_number)

    return metric_name

def gather_sku_info():
    global sku_list

    sku_list = dict()
    response = None

    try:
        logging.debug("gather_sku_info() - Check Access to OCI Public Rates URL (Required Internet Access)...")
        api_url = "https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/?currencyCode=USD"
        response = requests.get(api_url)
        logging.debug("gather_sku_info() - Success")
    except Exception:
        logging.warning("gather_sku_info() - Issue with Internet, List Price will no be extracted")

    logging.debug("response: " + str(response.json()))

    jsonData = response.json()
    items = jsonData['items']    

    for item in items:
        logging.debug("item.partNumber: " + item['partNumber'])
        logging.debug("item.metricName: " + item['metricName'])
        sku_list[item['partNumber']] = item['metricName']

    # Exception Handle
    sku_list['B89652'] = 'Gateway Per Hour'        

    logging.debug("sku_list: " + str(sku_list))
    
def get_formatted_float_str(float_number):
    float_str = f'{float_number:,.2f}'

    return float_str
        
def get_difference_float_str(before_amount, after_amount):
    difference = after_amount - before_amount
    difference_float_str = f'{difference:,.2f}'
    info = ''
    color = 'none'

    if difference_float_str == "0.00":
        pass
    elif difference_float_str == "-0.00":
        difference_float_str = "0.00"
    elif difference_float_str.startswith('-'):
        if before_amount != 0:
            info = (difference / before_amount) * 100
            info = f'{info:,.2f}' + '% ' + "<span class='glyphicon glyphicon-arrow-down'></span>"
        else:
            info = 'New'
        color = '#206AE5'
    else:
        difference_float_str = "+" + difference_float_str
        if before_amount != 0:      
            info = (difference / before_amount) * 100
            info = f'{info:,.2f}' + '% ' + "<span class='glyphicon glyphicon-arrow-up'></span>"
        else:
            info = 'New'            
        color = '#fc4c4e'

    logging.debug("after_amount: " + str(after_amount))
    logging.debug("before_amount: " + str(before_amount))
    logging.debug("difference: " + str(difference))        
    logging.debug("difference_float_str: " + str(difference_float_str))   

    return difference_float_str, info, color

def prep_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tenant_id', default='', dest='tenant_id',
                        help='The tenant where you want to get a daily cost report')
    parser.add_argument('--ons_topic_id', default='', dest='ons_topic_id',
                        help='The notification topic id where you want to publish a message for notifying ')
    parser.add_argument('--alert_threshold', default='', dest='alert_threshold',
                        help='The threshold which you want to notify it over than ')    
    parser.add_argument('--bucket_name', default='daily-costs-bucket', dest='bucket_name',
                        help='The bucket name which you want to upload the generated report')  
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
    logging.info('Report Daily Costs v{0}'.format(version))
    start_time = datetime.datetime.now()
    logging.info('Script execution start time: {0}'.format(
        start_time.replace(microsecond=0).isoformat()))    

    args = prep_arguments()

    if args is None:
        exit()    

    if args.ip == True:
        config = {}
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

        config = {'region': signer.region, 'tenancy': signer.tenancy_id}

        tenant_id = signer.tenancy_id

        identity_client = oci.identity.IdentityClient(config=config, signer=signer)
        notification_client = oci.ons.NotificationDataPlaneClient(config=config, signer=signer)
        usage_api_client = oci.usage_api.UsageapiClient(config=config, signer=signer)
        object_storage_client = oci.object_storage.ObjectStorageClient(config, signer=signer)
    else:
        config = oci.config.from_file()
        signer = None

        tenant_id = args.tenant_id

        identity_client = oci.identity.IdentityClient(config=config)
        notification_client = oci.ons.NotificationDataPlaneClient(config=config)
        usage_api_client = oci.usage_api.UsageapiClient(config=config)
        object_storage_client = oci.object_storage.ObjectStorageClient(config)

    ons_topic_id = args.ons_topic_id
    alert_threshold = float(args.alert_threshold)
    bucket_name = args.bucket_name

    logging.info(bucket_name)
    
    report_daily_costs_with_forecast(tenant_id, ons_topic_id, alert_threshold, bucket_name)
