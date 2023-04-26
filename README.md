# Report Daily Cost using Usage API and Notification


## Create a Notification Topic and Subscribe

1. Open the navigation menu and click **Developer Services**. Under **Application Integration**, click **Notifications**.

2. Click **Create Topic**. Enter the following:

    - Name: ex, `daily-cost-notification-topic`
    - Description(Optional): A friendly description. You can change this value later if you want to.

    Click **Create**

3. Click the created topic

4. Click **Create Subscription**. Enter the following:

    - Protocol: Email
    - Email: Your email address

    Click **Create**

5. Go to your email client. And click the received Subscription Confirmation email. And click the **Confirmation subscription** link.

6. Go back to OCI Console. Check if the state of your topic subscription is Active.

7. Copy the Topic OCID.

## Create a compute instance

1. Open the navigation menu and click Compute. Under Compute, click Instances

2. Create a compute instance

## Setup Report Daily Costs scripts

1. SSH into the instance

2. Install the Python OCI SDK

```
$ pip3 install oci
```

3. Copy the report_daily_costs source into /home/opc

```
$ git clone https://github.com/TheKoguryo/report_daily_costs.git
```

4. Create a cron job. In the terminal, type:

```
$ crontab -e
```

5. Type ``i`` to insert a new line.

6. Write your running schedule.

In my test, it is best to run the script every 6 AM GMT. If you run early, the cost will be increased until 6 AM GMT.

```
###############################################################################
# Crontab to run report_daily_costs
###############################################################################
0 6 * * * timeout 1h /home/opc/report_daily_costs/run_report_daily_costs.sh > /home/opc/report_daily_costs/run_report_daily_costs.sh_run.txt 2>&1
```

7. Save and close the file (ESC, then :x or :wq).

*Syntax of crontab:*

    * * * * * command to be executed
    - - - - -
    | | | | |
    | | | | ---- Day of week (0 - 7) (Sunday=0 or 7)
    | | | ------- Month (1 - 12)
    | | -------- Day of month (1 - 31)
    | ---------- Hour (0 - 23)
    ------------ Minute (0 - 59)

> You can also use a helper site such as https://crontab.guru to help you set the optimal execution times.

## Create a Policy for this compute to run the script.


## Related Documents

- [Use the Crontab Utility to Schedule Tasks on Oracle Linux](https://docs.oracle.com/en/learn/oracle-linux-crontab/index.html#before-you-begin)
