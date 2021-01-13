from datetime import datetime

TWITTER_DATE_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'


def transform_status(status):
    convert_dates(status)
    return status


def transform_user(user):
    convert_dates(user)
    return user


def convert_dates(data):
    # Convert dates at root of status
    if 'created_at' in data:
        data['created_at'] = datetime.strptime(data['created_at'], TWITTER_DATE_FORMAT)

    # Recursive call for user element
    if hasattr(data, 'user'):
        convert_dates(data['user'])

    # Recursive call for retweets and quoted tweets
    if 'quoted_status' in data:
        convert_dates(data['quoted_status'])
    if 'retweeted_status' in data:
        convert_dates(data['retweeted_status'])


def get_all_text(status):
    text = ''
    if 'retweeted_status' in status:
        text += get_all_text(status['retweeted_status'])

    if 'quoted_status' in status:
        text += get_all_text(status['quoted_status'])

    if 'extended_tweet' in status:
        text += status['extended_tweet']['full_text']
        for url in status['extended_tweet']['entities']['urls']:
            text += url['display_url']
    elif 'text' in status:
        text += status['text']
        for url in status['entities']['urls']:
            text += url['display_url']
    elif 'full_text' in status:
        text += status['full_text']
        for url in status['entities']['urls']:
            text += url['display_url']

    return text


def get_formatted_text(status):
    text = ''

    if 'retweeted_status' in status:
        text += ' RT @'
        text += status['retweeted_status']['user']['screen_name']
        text += ': '
        text += get_formatted_text(status['retweeted_status'])
        text += ' '

    if 'full_text' in status and not 'retweeted_status' in status:
        text += status['full_text']

    if 'text' in status and not 'retweeted_status' in status:
        text += status['text']

    return text
