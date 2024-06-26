'''
This Python script is a labor of love and has no formal support from Stack Overflow. 
If you run into difficulties, reach out to the person who provided you with this script.
Or, open an issue here: https://github.com/jklick-so/so4t_user_report/issues
'''

# Standard Python libraries
import argparse
import csv
import json
import os
# import pickle
import time
import statistics

# Local libraries
from so4t_api_v2 import V2Client
from so4t_api_v3 import V3Client
# from so4t_web_client import WebClient


def main():

    # Get command-line arguments
    args = get_args()

    if args.no_api:
        print("Skipping API calls and using data from JSON files in the data directory...")
        api_data = {}
        api_data['users'] = read_json('users.json')
        api_data['reputation_history'] = read_json('reputation_history.json')
        api_data['questions'] = read_json('questions.json')
        api_data['articles'] = read_json('articles.json')
        api_data['tags'] = read_json('tags.json')
        api_data['communities'] = read_json('communities.json')
        print("Data successfully loaded from JSON files.")
    else:
        api_data = get_api_data(args)

    if args.start_date:
        start_date = int(time.mktime(time.strptime(args.start_date, '%Y-%m-%d')))
    else:
        start_date = 0

    if args.end_date:
        end_date = int(time.mktime(time.strptime(args.end_date, '%Y-%m-%d')))
    else:
        end_date = 2524626000 # 2050-01-01

    users = process_api_data(api_data, start_date, end_date)
    export_to_json('processed_user_data', users)
    create_user_report(users, args.start_date, args.end_date)


def get_args():

    parser = argparse.ArgumentParser(
        prog='so4t_user_report.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Uses the Stack Overflow for Teams API to create \
        a CSV report with user metrics.',
        epilog = 'Example for Stack Overflow Business: \n'
                'python3 so4t_user_report.py --url "https://stackoverflowteams.com/c/TEAM-NAME" '
                '--token "YOUR_TOKEN" \n\n'
                'Example for Stack Overflow Enterprise: \n'
                'python3 so4t_user_report.py --url "https://SUBDOMAIN.stackenterprise.co" '
                '--key "YOUR_KEY" --token "YOUR_TOKEN"\n\n')
    
    parser.add_argument('--url', 
                        type=str,
                        help='[REQUIRED] Base URL for your Stack Overflow for Teams instance.')
    parser.add_argument('--token',
                        type=str,
                        help='[REQUIRED] API token for your Stack Overflow for Teams instance.')
    parser.add_argument('--key',
                    type=str,
                    help='API key value. Required if using Stack Overflow Enterprise.')
    parser.add_argument('--start-date',
                        type=str,
                        help='[OPTIONAL] Start date for filtering API data. '
                        'Must be YYYY-MM-DD format. '
                        'If not specified, all data will be included.')
    parser.add_argument('--end-date',
                        type=str,
                        help='[OPTIONAL] End date for filtering API data. '
                        'Must be YYYY-MM-DD format. '
                        'If not specified, all data will be included.')
    parser.add_argument('--no-api',
                        action='store_true',
                        help='Skips API calls and uses data from JSON files in the data directory.')
    # parser.add_argument('--web-client',
    #                     action='store_true',
    #                     help='Enables web-based data collection for data not available via API. Will '
    #                     'open a Chrome window and prompt user to login.')

    return parser.parse_args()


def get_api_data(args):

    # Only create a web session if the --web-client flag is used
    # if args.web_client:
    #     session_file = 'so4t_session'
    #     try:
    #         with open(session_file, 'rb') as f:
    #             web_client = pickle.load(f)
    #         if web_client.base_url != args.url or not web_client.test_session():
    #             raise FileNotFoundError # force creation of new session
    #     except FileNotFoundError:
    #         web_client = WebClient(args.url)
    #         with open(session_file, 'wb') as f:
    #             pickle.dump(web_client, f)
        
    # Instantiate V2Client and V3Client classes to make API calls
    v2client = V2Client(args.url, args.key, args.token)
    v3client = V3Client(args.url, args.token)
    
    # Get all questions, answers, comments, articles, tags, and SMEs via API
    so4t_data = {}
    so4t_data['users'] = get_users(v2client, v3client)
    so4t_data['reputation_history'] = get_reputation_history(v2client, so4t_data['users'])
    so4t_data['questions'] = get_questions_answers_comments(v2client) # also gets answers/comments
    so4t_data['articles'] = get_articles(v2client)
    so4t_data['tags'] = get_tags(v3client) # also gets tag SMEs

    # Get additional data via web scraping
    # if args.web_client:
    #     so4t_data['communities'] = web_client.get_communities()
    # else:
    #     so4t_data['communities'] = None

    # Export API data to JSON file
    for name, data in so4t_data.items():
        export_to_json(name, data)

    return so4t_data


def get_users(v2client, v3client):

    # Filter documentation: https://api.stackexchange.com/docs/filters
    if 'soedemo' in v2client.api_url: # for internal testing
        filter_string = ''
    elif v2client.soe: # Stack Overflow Enterprise requires the generation of a custom filter
        filter_attributes = [
            "user.is_deactivated" # this attribute is only available in Enterprise and in API v2
        ]
        filter_string = v2client.create_filter(filter_attributes)
    else: # Stack Overflow Business or Basic
        filter_string = ''

    v2_users = v2client.get_all_users(filter_string)

    # Exclude users with an ID of less than 1 (i.e. Community user and user groups)
    v2_users = [user for user in v2_users if user['user_id'] > 1]

    if 'soedemo' in v3client.api_url: # for internal testing only
        v2_users = [user for user in v2_users if user['user_id'] > 28000]

    v3_users = v3client.get_all_users()
    
    # Add additional user data from API v3 to user data from API v2
    # API v3 fields to add: 'email', 'jobTitle', 'department', 'externalId, 'role'
    for user in v2_users:
        for v3_user in v3_users:
            if user['user_id'] == v3_user['id']:
                user['email'] = v3_user['email']
                user['title'] = v3_user['jobTitle']
                user['department'] = v3_user['department']
                user['external_id'] = v3_user['externalId']
                if v3_user['role'] == 'Moderator':
                    user['moderator'] = True
                else:
                    user['moderator'] = False
                break
        try:
            user['moderator']
        except KeyError: # if user is not found in v3 data, it means they're a deactivated user
            # API v3 data can be obtained for deactivated users; it requires a separate API call
            v3_user = v3client.get_user(user['user_id'])
            user['email'] = v3_user['email']
            user['title'] = v3_user['jobTitle']
            user['department'] = v3_user['department']
            user['external_id'] = v3_user['externalId']
            user['is_deactivated'] = True

            if v3_user['role'] == 'Moderator':
                user['moderator'] = True
            else:
                user['moderator'] = False

    return v2_users


def get_reputation_history(v2client, users):

    user_ids = [user['user_id'] for user in users]
    reputation_history = v2client.get_reputation_history(user_ids)

    return reputation_history


def get_questions_answers_comments(v2client):
    
    # The API filter used for the /questions endpoint makes it so that the API returns
    # all answers and comments for each question. This is more efficient than making
    # separate API calls for answers and comments.
    # Filter documentation: https://api.stackexchange.com/docs/filters
    if v2client.soe: # Stack Overflow Enterprise requires the generation of a custom filter
        filter_attributes = [
            # "answer.body",
            # "answer.body_markdown",
            "answer.comment_count",
            "answer.comments",
            "answer.down_vote_count",
            "answer.last_editor",
            "answer.link",
            "answer.share_link",
            "answer.up_vote_count",
            # "comment.body",
            # "comment.body_markdown",
            "comment.link",
            "question.answers",
            # "question.body",
            # "question.body_markdown",
            "question.comment_count",
            "question.comments",
            "question.down_vote_count",
            "question.favorite_count",
            "question.last_editor",
            "question.notice",
            "question.share_link",
            "question.up_vote_count"
        ]
        filter_string = v2client.create_filter(filter_attributes)
    else: # Stack Overflow Business or Basic
        filter_string = '!X9DEEiFwy0OeSWoJzb.QMqab2wPSk.X2opZDa2L'
    questions = v2client.get_all_questions(filter_string)

    return questions


def get_articles(v2client):

    # Filter documentation: https://api.stackexchange.com/docs/filters
    if v2client.soe:
        filter_attributes = [
            # "article.body",
            # "article.body_markdown",
            "article.comment_count",
            "article.comments",
            "article.last_editor",
            "comment.body",
            "comment.body_markdown",
            "comment.link"
        ]
        filter_string = v2client.create_filter(filter_attributes)
    else: # Stack Overflow Business or Basic
        filter_string = '!*Mg4Pjg9LXr9d_(v'

    articles = v2client.get_all_articles(filter_string)

    return articles


def get_tags(v3client):

    # While API v2 is more robust for collecting tag data, it does not return the tag ID field, 
    # which is needed to get the SMEs for each tag. Therefore, API v3 is used to get the tag ID
    tags = v3client.get_all_tags()

    # Get subject matter experts (SMEs) for each tag. This API call is only available in v3.
    # There's no way to get SME configurations in bulk, so this call must be made for each tag
    for tag in tags:
        if tag['subjectMatterExpertCount'] > 0:
            tag['smes'] = v3client.get_tag_smes(tag['id']) 
        else:
            tag['smes'] = {'users': [], 'userGroups': []}

    return tags


def process_api_data(api_data, start_date, end_date):

    users = api_data['users']
    users = add_new_user_fields(users)
    users = process_tags(users, api_data['tags'])
    users = process_questions(users, api_data['questions'])
    users = process_articles(users, api_data['articles'])
    users = process_reputation_history(users, api_data['reputation_history'])
    users = process_users(users, start_date, end_date)

    # tags = process_communities(tags, api_data.get('communities'))

    export_to_json('user_metrics', users)
    
    return users


def add_new_user_fields(users):

    for user in users:
        user['questions'] = []
        user['question_count'] = 0
        user['questions_with_no_answers'] = 0
        user['question_upvotes'] = 0
        user['question_downvotes'] = 0

        user['answers'] = []
        user['answer_count'] = 0
        user['answer_upvotes'] = 0
        user['answer_downvotes'] = 0
        user['answers_accepted'] = 0
        user['answer_response_times'] = []
        user['answer_response_time_median'] = 0

        user['articles'] = []
        user['article_count'] = 0
        user['article_upvotes'] = 0

        user['comments'] = []
        user['comment_count'] = 0

        user['total_upvotes'] = 0
        user['reputation_history'] = []
        user['net_reputation'] = 0

        user['searches'] = []
        user['communities'] = []
        user['sme_tags'] = []
        user['watched_tags'] = []

        user['account_longevity_days'] = round(
            (time.time() - user['creation_date'])/60/60/24)
        user['account_inactivity_days'] = round(
            (time.time() - user['last_access_date'])/60/60/24)
        
        try:
            if user['is_deactivated']:
                user['account_status'] = 'Deactivated'
            else:
                user['account_status'] = 'Active'
        except KeyError: # Stack Overflow Business or Basic
            user['account_status'] = 'Registered'
    return users


def process_reputation_history(users, reputation_history):

    for user in users:
        for event in reputation_history:
            if event['user_id'] == user['user_id']:
                    user['reputation_history'].append(event)

    return users


def process_tags(users, tags):
    '''
    Iterate through each tag, find the SMEs, and add the tag name to a new field
    on the user object, indicating which tags they're a SME for
    In some situations, a user may be listed as both an individual SME and a group SME
    '''
    for tag in tags:
        for user in users:
            for sme in tag['smes']['users']:
                if user['user_id'] == sme['id']:
                    user['sme_tags'].append(tag['name'])
                    continue # if user is an individual SME, skip the group SME check
            for sme in tag['smes']['userGroups']:
                if user['user_id'] == sme['id']:
                    user['sme_tags'].append(tag['name'])
        
    return users


def process_questions(users, questions):

    for question in questions:
        asker_id = validate_user_id(question['owner'])
        user_index = get_user_index(users, asker_id)

        if user_index == None: # if user was deleted, add them to the list
            deleted_user = initialize_deleted_user(asker_id, question['owner']['display_name'])
            users.append(deleted_user)
            user_index = get_user_index(users, asker_id)

        users[user_index]['questions'].append(question)

        if question.get('answers'):
            users = process_answers(users, question['answers'], question)

        if question.get('comments'):
            users = process_comments(users, question)

    return users

        
def process_answers(users, answers, question):

    for answer in answers:
        answerer_id = validate_user_id(answer['owner'])
        user_index = get_user_index(users, answerer_id)

        if user_index == None:
            deleted_user = initialize_deleted_user(answerer_id, answer['owner']['display_name'])
            users.append(deleted_user)
            user_index = get_user_index(users, answerer_id)

        users[user_index]['answers'].append(answer)
        answer_response_time_hours = (answer['creation_date'] - question['creation_date'])/60/60
        users[user_index]['answer_response_times'].append(answer_response_time_hours)

        if answer.get('comments'):
            users = process_comments(users, answer)

    return users


def process_comments(users, object_with_comments):

    for comment in object_with_comments['comments']:
        commenter_id = validate_user_id(comment['owner'])
        user_index = get_user_index(users, commenter_id)

        if user_index == None:
            deleted_user = initialize_deleted_user(commenter_id, comment['owner']['display_name'])
            users.append(deleted_user)
            user_index = get_user_index(users, commenter_id)

        users[user_index]['comments'].append(comment)

    return users


def process_articles(users, articles):

    for article in articles:
        author_id = validate_user_id(article['owner'])
        user_index = get_user_index(users, author_id)
        if user_index == None:
            deleted_user = initialize_deleted_user(author_id, article['owner']['display_name'])
            users.append(deleted_user)
            user_index = get_user_index(users, author_id)

        users[user_index]['articles'].append(article)

        # As of 2023.05.23, Article comments are slightly innaccurate due to a bug in the API
        # if article.get('comments'):
        #     for comment in article['comments']:
        #         commenter_id = validate_user_id(comment)
        #         tag_contributors[tag]['commenters'] = add_user_to_list(
        #             commenter_id, tag_contributors[tag]['commenters']
        #         )
        
    return users


def process_users(users, start_date, end_date):


    for user in users:
        for question in user['questions']:
            if question['creation_date'] > start_date and question['creation_date'] < end_date:
                user['question_count'] += 1
                user['question_upvotes'] += question['up_vote_count']
                user['question_downvotes'] += question['down_vote_count']
                if question['answer_count'] == 0:
                    user['questions_with_no_answers'] += 1

        for answer in user['answers']:
            if answer['creation_date'] > start_date and answer['creation_date'] < end_date:
                user['answer_count'] += 1
                user['answer_upvotes'] += answer['up_vote_count']
                user['answer_downvotes'] += answer['down_vote_count']
                if answer['is_accepted']:
                    user['answers_accepted'] += 1

        for article in user['articles']:
            if article['creation_date'] > start_date and article['creation_date'] < end_date:
                user['article_count'] += 1
                user['article_upvotes'] += article['score']

        for comment in user['comments']:
            if comment['creation_date'] > start_date and comment['creation_date'] < end_date:
                user['comment_count'] += 1

        for event in user['reputation_history']:
            if event['creation_date'] > start_date and event['creation_date'] < end_date:
                user['net_reputation'] += event['reputation_change']

        for answer_response_time in user['answer_response_times']:
            if answer_response_time <= 0:
                user['answer_response_times'].remove(answer_response_time)

        if user['answer_response_times']:
            user['answer_response_time_median'] = round(
                statistics.median(user['answer_response_times']), 2)
        else:
            user['answer_response_time_median'] = ''

        user['total_upvotes'] = user['question_upvotes'] + user['answer_upvotes'] + \
            user['article_upvotes']
        user['total_downvotes'] = user['question_downvotes'] + user['answer_downvotes']

    return users


def create_user_report(users, start_date, end_date):

    # Create a list of user dictionaries, sorted by net reputation
    sorted_users = sorted(users, key=lambda k: k['net_reputation'], reverse=True)

    # Select fields for the user report
    user_metrics = []
    for user in sorted_users:
        try:
            user_metric = {
                'User ID': user['user_id'],
                'Display Name': user['display_name'],
                'Net Reputation': user['net_reputation'],
                'Account Longevity (Days)': user['account_longevity_days'],
                'Account Inactivity (Days)': user['account_inactivity_days'],

                'Questions': user['question_count'],
                'Questions With No Answers': user['questions_with_no_answers'],
                # 'Question Upvotes': user['question_upvotes'],
                # 'Question Downvotes': user['question_downvotes'],

                'Answers': user['answer_count'],
                # 'Answer Upvotes': user['answer_upvotes'],
                # 'Answer Downvotes': user['answer_downvotes'],
                'Answers Accepted': user['answers_accepted'],
                'Median Answer Time (Hours)': user['answer_response_time_median'],

                'Articles': user['article_count'],
                # 'Article Upvotes': user['article_upvotes'],

                'Comments': user['comment_count'],

                'Total Upvotes': user['total_upvotes'],
                'Total Downvotes': user['total_downvotes'],

                # 'Searches': user['searches'],
                # 'Communities': user['communities'],
                'SME Tags': ', '.join(user['sme_tags']),
                # 'Watched Tags': user['watched_tags'],

                'Account Status': user['account_status'],
                'Moderator': user['moderator'],

                'Email': user['email'],
                'Title': user['title'],
                'Department': user['department'],
                'External ID': user['external_id'],
                'Account ID': user['account_id']
            }
        except KeyError as e:
            print(f"KeyError: missing [{e.args[0]}] key for user {user['user_id']}")
            print(f"Link to user: {user.get('link')}")
            print("Data for this user will not be included in the report.")
            print("\n")
            input("Press Enter to continue...")
            continue
        user_metrics.append(user_metric)
    

    # Export user metrics to CSV
    if start_date and end_date:
        export_to_csv(f'user_metrics_{start_date}_to_{end_date}', user_metrics)
    else:
        export_to_csv('user_metrics', user_metrics)


def get_user_index(users, user_id):

    for index, user in enumerate(users):
        if user['user_id'] == user_id:
            return index
    
    return None # if user is not found


def initialize_deleted_user(user_id, display_name):

    user = {
        'user_id': user_id,
        'display_name': f"{display_name} (DELETED)",

        'questions': [],
        'question_count': 0,
        'questions_with_no_answers': 0,
        'question_upvotes': 0,
        'question_downvotes': 0,

        'answers': [],
        'answer_count': 0,
        'answer_upvotes': 0,
        'answer_downvotes': 0,
        'answers_accepted': 0,
        'answer_response_times': [],

        'articles': [],
        'article_count': 0,
        'article_upvotes': 0,

        'comments': [],
        'comment_count': 0,

        'total_upvotes': 0,
        'reputation_history': [],
        'net_reputation': 0,

        'searches': [],
        'communities': [],
        'sme_tags': [],
        'watched_tags': [],
        
        'moderator': '',
        'email': '',
        'title': '',
        'department': '',
        'external_id': '',
        'account_id': '',
        'account_longevity_days': '',
        'account_inactivity_days': '',
        'account_status': 'Deleted'
    }

    return user


def validate_user_id(user):
    """
    Checks to see if a user_id is present. If not, the user has been deleted. In this case, the
    user_id can be extracted from the display_name. For example, if a deleted user's display_name
    is 'user123', the user_id will be 123."""

    try:
        user_id = user['user_id']
    except KeyError: # if user_id is not present, the user was deleted
        try:
            user_id = int(user['display_name'].split('user')[1])
        except IndexError:
            # This shouldn't happen, but if it does, the user_id will be the display name
            # This seems to only happen in the internal testing environment
            user_id = user['display_name']

    return user_id


def export_to_csv(data_name, data):

    date = time.strftime("%Y-%m-%d")
    file_name = f"{date}_{data_name}.csv"

    csv_header = [header for header in list(data[0].keys())]
    with open(file_name, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(csv_header)
        for tag_data in data:
            writer.writerow(list(tag_data.values()))
        
    print(f'CSV file created: {file_name}')


def export_to_json(data_name, data):
    
    file_name = data_name + '.json'
    directory = 'data'

    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = os.path.join(directory, file_name)

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

    print(f'JSON file created: {file_name}')


def read_json(file_name):
    
    directory = 'data'
    file_path = os.path.join(directory, file_name)
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        raise FileNotFoundError
    
    return data


if __name__ == '__main__':

    main()
