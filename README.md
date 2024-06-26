# Stack Overflow for Teams User Report (so4t_user_report)
A Python script that uses the Stack Overflow for Teams API to create a CSV report of how well each user is performing. You can see an example of what the output looks like in the Examples directory ([here](https://github.com/jklick-so/so4t_user_report/blob/main/Examples/user_metrics.csv)).

## Table of Contents
* [Requirements](https://github.com/jklick-so/so4t_user_report?tab=readme-ov-file#requirements)
* [Setup](https://github.com/jklick-so/so4t_user_report?tab=readme-ov-file#setup)
* [Basic Usage](https://github.com/jklick-so/so4t_user_report?tab=readme-ov-file#basic-usage)
* [Advanced Usage](https://github.com/jklick-so/so4t_user_report?tab=readme-ov-file#advanced-usage)
  * [`--start-date` and `--end-date`](https://github.com/jklick-so/so4t_user_report?tab=readme-ov-file#--start-date-and---end-date)
  * [`--no-api`](https://github.com/jklick-so/so4t_user_report?tab=readme-ov-file#--no-api)
* [Support, security, and legal](https://github.com/jklick-so/so4t_user_report?tab=readme-ov-file#support-security-and-legal)

## Requirements
* A Stack Overflow for Teams instance (Basic, Business, or Enterprise); for Enterprise, version 2023.3 or later
* Python 3.8 or higher ([download](https://www.python.org/downloads/))
* Operating system: Linux, MacOS, or Windows

If using the `--web-client` argument, there are additional requirements (details in [Advanced Usage](https://github.com/jklick-so/so4t_user_report#--web-client) section)

## Setup

[Download](https://github.com/jklick-so/so4t_user_report/archive/refs/heads/account_id_keyerror.zip) and unpack the contents of this repository

**Installing Dependencies**

* Open a terminal window (or, for Windows, a command prompt)
* Navigate to the directory where you unpacked the files
* Install the dependencies: `pip3 install -r requirements.txt`

**API Authentication**

For the Basic and Business tiers, you'll need an API token. For Enterprise, you'll need to obtain both an API key and an API token.

* For Basic or Business, instructions for creating a personal access token (PAT) can be found in [this KB article](https://stackoverflow.help/en/articles/4385859-stack-overflow-for-teams-api).
* For Enterprise, documentation for creating the key and token can be found within your instance, at this url: `https://[your_site]/api/docs/authentication`

Creating an access token for Enterpise can sometimes be tricky for people who haven't done it before. Here are some (hopefully) straightforward instructions:
* Go to the page where you created your API key. Take note of the "Client ID" associated with your API key.
* Go to the following URL, replacing the base URL, the `client_id`, and base URL of the `redirect_uri` with your own:
`https://YOUR.SO-ENTERPRISE.URL/oauth/dialog?client_id=111&redirect_uri=https://YOUR.SO-ENTERPRISE.URL/oauth/login_success`
* You may be prompted to login to Stack Overflow Enterprise, if you're not already. Either way, you'll be redirected to a page that simply says "Authorizing Application"
* In the URL of that page, you'll find your access token. Example: `https://YOUR.SO-ENTERPRISE.URL/oauth/login_success#access_token=YOUR_TOKEN`

## Basic Usage

In a terminal window, navigate to the directory where you unpacked the script. 
Run the script using the following format, replacing the URL, token, and/or key with your own:
* For Basic and Business: `python3 so4t_user_report.py --url "https://stackoverflowteams.com/c/TEAM-NAME" --token "YOUR_TOKEN"`
* For Enterprise: `python3 so4t_user_report.py --url "https://SUBDOMAIN.stackenterprise.co" --key "YOUR_KEY" --token "YOUR_TOKEN"`

The script can take several minutes to run, particularly as it gathers data via the API. As it runs, it will continue to update the terminal window with the tasks it's performing.

When the script completes, it will indicate the CSV has been exported, along with the name of file. You can see an example of what the output looks like [here](https://github.com/jklick-so/so4t_user_report/blob/main/Examples/user_metrics.csv).

## Advanced Usage

There are some additional arguments you can add to the command line to customize the script's behavior, which are described below. All arguments (and instructions) can also be found by running the `--help` argument: `python3 so4t_user_report.py --help` 

### `--start-date` and `--end-date`

By default, the CSV report aggregates all historical data for users. If you'd like to filter this based on a certain amount of history, the `--start-date` and `--end-date` arguments allow you to take a slice of that history. Using these arguments would look like this:
`python3 so4t_user_report.py --url "https://SUBDOMAIN.stackenterprise.co" --key "YOUR_KEY" --token "YOUR_TOKEN" --start-date "2022-01-01" --end-date "2022-12-31"`
* The date format is `YYYY-MM-DD`. 
* When using a start date without an end date, the script will use the current date as the end date.
* When using an end date without a start date, the script will use the earliest date available in the data as the start date.

### `--no-api`

In conjunction with the `--start-date` and `--end-date` arguments, `--no-api` allows you to use leverage preexisting JSON data from previous execution of this script. This is significantly faster than running all the API calls again; in fact, it's nearly instantaneous. If you were looking to generate user metrics based on a variety of time ranges, using the `--no-api` argument sigificantly speeds up the process. 

Using `--no-api` would look like this: `python3 so4t_user_report.py --no-api --start-date "2022-01-01" --end-date "2022-12-31"`

> Note: when using `--no-api`, the `--url`, `--key`, and `--token` arguments are unecessary. When you'd like to update the JSON data via fresh API calls, simply remove the `no-api` argument and add back the required authentication arguments.

## Support, security, and legal
Disclaimer: the creator of this project works at Stack Overflow, but it is a labor of love that comes with no formal support from Stack Overflow. 

If you run into issues using the script, please [open an issue](https://github.com/jklick-so/so4t_user_report/issues). You are also welcome to edit the script to suit your needs, steal the code, or do whatever you want with it. It is provided as-is, with no warranty or guarantee of any kind. If the creator wasn't so lazy, there would likely be an MIT license file included.

All data is handled locally on the device from which the script is run. The script does not transmit data to other parties, such as Stack Overflow. All of the API calls performed are read only, so there is no risk of editing or adding content on your Stack Overflow for Teams instance.
