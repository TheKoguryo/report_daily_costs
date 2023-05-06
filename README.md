# Report Daily Cost using Usage API and Notification

*Do this steps in your home region.*


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


## Create a Policy for this compute to run the script.

1. Login to your OCI Cloud console

2. Create new Policy: scheduled-report-daily-costs-policy with Statements:

    - Update the statement with your compute instance id

    ```
    allow any-user to read usage-reports in tenancy where request.instance.id='ocid1.instance.oc1.iad.aaaaaaaa.....'
    allow any-user to use ons-family in tenancy where request.instance.id='ocid1.instance.oc1.iad.aaaaaaaa.....'
    ```

## Setup Report Daily Costs scripts

1. SSH into the instance

2. Install the Python OCI SDK

    ```
    pip3 install oci
    ```

3. Copy the report_daily_costs source into /home/opc

    ```
    sudo dnf install git
    git clone https://github.com/TheKoguryo/report_daily_costs.git
    ```

4. Update the value of ONS_TOPIC_ID to your Topic OCID in run_report_daily_costs.sh

    ```
    export ONS_TOPIC_ID=ocid1.onstopic.oc1.iad.aaaaaaaa.....
    ```

5. Update the value of alert-threshold in run_report_daily_costs.sh

    ```
    # cron schedule - 0 * * * * 
    # Notify at 23:00
    #
    # Check the yesterday's cost every hours that is under being calculated.
    # If that cost is more than the cost of the day before yesterday and the difference is over threshold, notify at that time.
    python3 $APPDIR/report_daily_costs.py -ip --ons_topic_id $ONS_TOPIC_ID --alert-threshold 50
    ```

6. Create a cron job. In the terminal, type:

    ```
    crontab -e
    ```

7. Type ``i`` to insert a new line.

8. Write your running schedule.

    I recommend a cron schedule to every hour.

    ```
    ###############################################################################
    # Crontab to run report_daily_costs
    ###############################################################################
    0 * * * * timeout 1h /home/opc/report_daily_costs/run_report_daily_costs.sh >> /home/opc/report_daily_costs/run_report_daily_costs.sh_run.txt 2>&1
    ```

    *Syntax of crontab:*
    
        * * * * * command to be executed
        - - - - -
        | | | | |
        | | | | ---- Day of week (0 - 7) (Sunday=0 or 7)
        | | | ------ Month (1 - 12)
        | | -------- Day of month (1 - 31)
        | ---------- Hour (0 - 23)
        ------------ Minute (0 - 59)

    > You can also use a helper site such as https://crontab.guru to help you set the optimal execution times.

9. Save and close the file (ESC, then :x or :wq).

10. When the cost is more than thread or At 23:00 Every day. 

[Notification Email](notification-email.png)


## Related Documents

- [Use the Crontab Utility to Schedule Tasks on Oracle Linux](https://docs.oracle.com/en/learn/oracle-linux-crontab/index.html#before-you-begin)
