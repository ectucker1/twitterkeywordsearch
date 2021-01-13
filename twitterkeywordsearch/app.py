from dotenv import load_dotenv, find_dotenv
import tweepy
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import argparse
from twitterkeywordsearch.query import load_query
from twitterkeywordsearch.data_transform import transform_status, get_formatted_text


def main():
    # Load environment variables
    load_dotenv(find_dotenv())

    # Parse command line arguments
    args = parse_arguments()

    # Load and validate the query
    query = load_query(args.query)

    # Create database and twitter connections
    db = connect_database()
    api = create_twitter_api()

    # Pick which data to download based on the mode
    if args.mode == 'search':
        # Perform the search
        search_tweets(db[args.outcollection], api, query, args.sort, args.target)
    elif args.mode == 'users':
        print('User download mode not yet implemented')


def search_tweets(collection, api, query, sort, target_count):
    # Track the number of results found so far
    found = 0
    # Call the search method, and iterate over results
    for status in tweepy.Cursor(api.search, q=query, lang="en", result_type=sort,
                                monitor_rate_limit=True, wait_on_rate_limit=True, wait_on_rate_limit_notify=True,
                                retry_count=5, retry_delay=5).items():
        # Get raw JSON data of status
        json = transform_status(status._json)

        # Save the status to the database
        collection.insert_one(json)

        # Increment the number of statuses
        found += 1
        if found >= target_count:
            break


def parse_arguments():
    parser = argparse.ArgumentParser(description='Download or stream data from Twitter to a MongoDB database.')
    parser.add_argument('mode', choices=['search', 'users'],
                        help='the mode to run the program in')
    parser.add_argument('--query', '-q', default='search.txt',
                        help='path to a file with a list of keywords to search for (default: %(default)s)')
    parser.add_argument('--sort', '-s', default='popular', choices=['popular', 'recent', 'mixed'],
                        help='whether to favor popular tweets, recent tweets, or a mix (default: %(default)s)')
    parser.add_argument('--target', '-t', type=int, default=100000,
                        help='the number of Tweets to stop after downloading (default: %(default)s)')
    parser.add_argument('--incollection', '-i', default='search',
                        help='the MongoDB collection to read a list of users from (default: %(default)s)')
    parser.add_argument('--outcollection', '-o', default='search',
                        help='the MongoDB collection to save the search results or user information to (default: %(default)s)')
    return parser.parse_args()


def create_twitter_api():
    try:
        auth = tweepy.OAuthHandler(os.getenv('TWITTER_API_KEY'), os.getenv('TWITTER_API_SECRET'))
        auth.set_access_token(os.getenv('TWITTER_ACCESS_TOKEN'), os.getenv('TWITTER_TOKEN_SECRET'))
        return tweepy.API(auth)
    except tweepy.TweepError:
        print('Could not connect to twitter API.')


def connect_database():
    try:
        client = MongoClient(os.getenv('DATABASE_URL'), serverSelectionTimeoutMS=10)
        client.server_info()
        return client.twitter
    except ServerSelectionTimeoutError:
        print('Could not connect to database.')
        exit(1)
