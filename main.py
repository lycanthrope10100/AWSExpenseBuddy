import datetime
import requests
import json
import boto3

account_information = [
    {
        "account_number": "<your_account_id>",
        "region": "<your_account_region>",
        "Filter": {"And": [
            {"Tags": {
                'Key': 'techteam',
                'Values': [
                    'team1', 'team2'
                ],
                'MatchOptions': [
                    'EQUALS',
                ]
            }},
            {"Not": {"Dimensions": {"Key": "RECORD_TYPE",
                                    "Values": ["Refund", "Tax", "Enterprise Discount Program Discount", "Private Rate Card Discount"]}}}
        ]
        },
        "slack_channels": ["#<slack_channel_name1>","#<slack_channel_name2>"],
        "mop_USD": <your_mop_budget>,
        "aws_profile": "<your_aws_profile>"
    },
]

def get_number_of_days_in_current_month():

    current_date = datetime.date.today()

    if current_date.month == 12:
        next_month = 1
        next_year = current_date.year + 1
    else:
        next_month = current_date.month + 1
        next_year = current_date.year

    number_of_days_in_current_month = (datetime.date(next_year, next_month, 1) - datetime.timedelta(days=1)).day

    return number_of_days_in_current_month

def send_message_to_slack(slack_channel, message):

    if slack_channel == "#<slack_channel_name1>":
        webhook_url = "#<slack_webhook_url1>"
    elif slack_channel == "#<slack_channel_name2>":
        webhook_url = "#<slack_webhook_url2>"
    else:
        webhook_url = "#<slack_webhook_url1>"

    payload = {
        "channel": slack_channel,
        "text": message,
        "mrkdwn": True
    }

    headers = {
        "Content-type": "application/json"
    }

    response = requests.post(
        webhook_url, data=json.dumps(payload), headers=headers)

    print(response)
    if response.status_code == 200:
        print("Message sent successfully to Slack!")
    else:
        print(
            f"Failed to send message to Slack. Status code: {response.status_code}, Response: {response.text}")


def compare_costs(yesterday_cost, day_before_yesterday_cost):

    cost_difference = yesterday_cost - day_before_yesterday_cost

    if day_before_yesterday_cost == 0 or day_before_yesterday_cost == 0.0:
        cost_change_percentage = "NA"
    else:
        cost_change_percentage = (
            cost_difference / day_before_yesterday_cost) * 100

    return cost_difference, cost_change_percentage

def get_last_two_month_names():

    current_date = datetime.date.today()

    last_month = current_date.replace(day=1) - datetime.timedelta(days=1)
    last_to_last_month = last_month.replace(day=1) - datetime.timedelta(days=1)

    last_month_full_name = last_month.strftime('%B') + " " + last_month.strftime('%Y')
    last_to_last_month_full_name = last_to_last_month.strftime('%B') + " " + last_to_last_month.strftime('%Y')

    return last_month_full_name, last_to_last_month_full_name

def get_daily_cost(region, filter, profile):

    if profile != "default":
        session = boto3.Session(profile_name=profile)
        client = session.client('ce', region_name=region)
    else:
        client = boto3.client('ce', region_name=region)

    current_date = datetime.date.today()

    to_date = current_date - datetime.timedelta(days=1)
    from_date = current_date - datetime.timedelta(days=3)

    daily_cost_response = client.get_cost_and_usage(
        TimePeriod={
            'Start': from_date.isoformat(),
            'End': to_date.isoformat()
        },
        Filter=filter,
        Granularity='DAILY',
        Metrics=['AmortizedCost']
    )

    costs = daily_cost_response['ResultsByTime']

    day_before_yesterday_cost = float(costs[0]['Total']['AmortizedCost']['Amount'])
    yesterday_cost = float(costs[1]['Total']['AmortizedCost']['Amount'])

    daily_cost_response_by_service = client.get_cost_and_usage(
        TimePeriod={
            'Start': from_date.isoformat(),
            'End': to_date.isoformat()
        },
        Filter=filter,
        Granularity='DAILY',
        Metrics=['AmortizedCost'],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ]
    )

    services_by_cost = sorted(daily_cost_response_by_service['ResultsByTime'][1]['Groups'], key=lambda x: float(x['Metrics']['AmortizedCost']['Amount']), reverse=True)[:10]

    top_10_services_by_cost = "\n".join(
    f"{index}. {service['Keys'][0]} : ${float(service['Metrics']['AmortizedCost']['Amount']):.2f}"
    for index, service in enumerate(services_by_cost, start=1)
    )

    day_before_yesterday_date = str(current_date - datetime.timedelta(days=2))

    return yesterday_cost, day_before_yesterday_cost, top_10_services_by_cost, day_before_yesterday_date

def get_monthly_cost(region, filter, profile):
    if profile != "default":
        session = boto3.Session(profile_name=profile)
        client = session.client('ce', region_name=region)
    else:
        client = boto3.client('ce', region_name=region)

    current_date = datetime.date.today()

    to_date = current_date.replace(day=1)
    first_day_of_last_month = (to_date - datetime.timedelta(days=1)).replace(day=1)
    from_date = (first_day_of_last_month - datetime.timedelta(days=1)).replace(day=1)

    monthly_cost_response = client.get_cost_and_usage(
        TimePeriod={
            'Start': from_date.isoformat(),
            'End': to_date.isoformat()
        },
        Filter=filter,
        Granularity='MONTHLY',
        Metrics=['AmortizedCost']
    )

    costs = monthly_cost_response['ResultsByTime']

    last_to_last_month_cost = float(costs[0]["Total"]["AmortizedCost"]["Amount"])
    last_month_cost= float(costs[1]["Total"]["AmortizedCost"]["Amount"])

    return last_month_cost, last_to_last_month_cost

def main():

    for account_info in account_information:
        account_number = account_info["account_number"]
        region = account_info["region"]
        filter = account_info["Filter"]
        slack_channels = account_info["slack_channels"]
        mop_USD = account_info["mop_USD"]
        aws_profile = account_info["aws_profile"]

        number_of_days_in_month = get_number_of_days_in_current_month()

        dop_USD = int(mop_USD) / int(number_of_days_in_month)

        yesterday_cost, day_before_yesterday_cost, top_10_services_by_cost, day_before_yesterday_date = get_daily_cost(region=region, filter=filter, profile=aws_profile)

        cost_difference = 0
        cost_change_percentage = 0
        cost_difference, cost_change_percentage = compare_costs(yesterday_cost, day_before_yesterday_cost)

        dop_delta = dop_USD - yesterday_cost
        dop_analysis = "Yesterday's Cost is below DOP" if (yesterday_cost < dop_USD) else "Yesterday's Cost is above DOP by $" + str(abs(round(dop_delta, 2)))

        last_month_cost, last_to_last_month_cost = get_monthly_cost(region=region, filter=filter, profile=aws_profile)
        last_month_full_name, last_to_last_month_full_name = get_last_two_month_names()

        mop_delta = mop_USD - last_month_cost
        mop_analysis = last_month_full_name + " Cost is below MOP " if (
                last_month_cost < mop_USD) else last_month_full_name + " Cost is above MOP by $" + str(abs(round(mop_delta, 2)))

        current_date = datetime.date.today()
        slack_message = f"""
===========================================
REPOR GENERATED ON {current_date} :-
Account Number                      : {account_number}
MOP                                 : ${mop_USD}
DOP                                 : ${round(dop_USD, 2)}
===========================================
LAST 2 DAYS COST DETAILS :-
Yesterday's Cost                    : ${round(yesterday_cost, 2)}
Day Before Yesterday's Cost         : ${round(day_before_yesterday_cost, 2)}
Cost Difference                     : ${round(cost_difference, 2)}
Cost Difference Percentage          : ${round(cost_change_percentage, 2)}
DOP Analysis                        : {dop_analysis}
===========================================
LAST 2 MONTHS COST DETAILS :-
{last_month_full_name.ljust(35)} : ${round(last_month_cost, 2)}
{last_to_last_month_full_name.ljust(35)} : ${round(last_to_last_month_cost, 2)}
MOP Analysis                        : {mop_analysis}
===========================================
TOP 10 SERVICES BY COST ON {day_before_yesterday_date} :-
{top_10_services_by_cost}
        """
        for slack_channel in slack_channels:
            pass
            send_message_to_slack(slack_channel, slack_message)

# Check if the script is being executed directly
if __name__ == "__main__":
    main()
