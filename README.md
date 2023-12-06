# AWSExpenseBuddy
Your go-to for AWS expense breakdowns. Get daily and monthly cost analysis based on daily (DOP) and monthly (MOP) operating plans, top service expenditures, and track spending trends to optimize your AWS budget effectively. Plus, receive updates on Slack for seamless collaboration and quick decision-making.

## Usage:
* Put main.py under cron
```bash
00 10 * * * python3 /path/to/main.py
```

## Debugging:
* Replace the <placeholders> in the code with the value, actual links and creds.
```bash
Line 8 - "account_number": "<your_account_id>",
Line 9 - "region": "<your_account_region>",
Line 11-21 - //Adjust to fit your specific requirements.
Line 24 - "slack_channels": ["#<slack_channel_name1>","#<slack_channel_name2>"],
Line 25 - "mop_USD": <your_mop_budget>, //Replace <your_mop_budget> with this value : (Annual_Operating_Plan_Or_Budget/12)
Line 26 - "aws_profile": "<your_aws_profile>" //Replace <your_aws_profile> with the corresponding profile from your ~/.aws/credentials
Line 47 - if slack_channel == "#<slack_channel_name1>":
Line 48 - webhook_url = "#<slack_webhook_url1>"
Line 49 - elif slack_channel == "#<slack_channel_name2>":
Line 50 - webhook_url = "#<slack_webhook_url2>"
Line 52 - webhook_url = "#<slack_webhook_url1>"
```
  
## Sample:
![.](https://github.com/lycanthrope10100/AWSExpenseBuddy/blob/master/Image.jpg)
