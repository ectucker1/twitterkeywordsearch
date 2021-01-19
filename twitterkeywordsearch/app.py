from dotenv import load_dotenv, find_dotenv
import tweepy
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import argparse
from twitterkeywordsearch.query import load_query
from twitterkeywordsearch.data_transform import transform_status, get_formatted_text
from twitterkeywordsearch.user_download import download_profile, download_tweets, download_follower_ids, download_following_ids
from threading import Thread


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
        download_users(db[args.incollection], db[args.outcollection], api)


def search_tweets(collection, api, query, sort, target_count):
    # Track the number of results found so far
    found = 0
    # Call the search method, and iterate over results
    for status in tweepy.Cursor(api.search, q=query, lang="en", result_type=sort, tweet_mode="extended",
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


def download_users(input_collection, output_collection, api):
    # Get the IDs of all users in the input collection
    users = set()
    for tweet in input_collection.find():
        users.add(tweet['user']['id_str'])

    # For each user in that collection
    for user in users:
        # If there is not already a document for that user in the output
        if output_collection.count_documents({'id_str': user}) < 1:
            # Add a document with that user ID to the collection
            output_collection.insert_one({'id_str': user})

    # Create a thread for each piece of info to be downloaded
    profile_thread = Thread(target=process_profile, daemon=True, args=(users, output_collection, api))
    tweet_thread = Thread(target=process_tweets, daemon=True, args=(users, output_collection, api))
    followers_thread = Thread(target=process_followers, daemon=True, args=(users, output_collection, api))
    following_thread = Thread(target=process_following, daemon=True, args=(users, output_collection, api))

    # Start up all the threads to download data
    profile_thread.start()
    tweet_thread.start()
    followers_thread.start()
    following_thread.start()

    # Wait for all threads to finish downloading
    profile_thread.join()
    tweet_thread.join()
    followers_thread.join()
    following_thread.join()


def process_tweets(users, output_collection, api):
    # For each user
    for user in users:
        # If there is not already a document for that user that has tweets
        if output_collection.count_documents({'id_str': user, 'tweets': {'$exists': True}}) < 1:
            print(f"Downloading tweets for ${user}")
            # Download the list of the user's tweets
            tweets = download_tweets(api, user)
            if tweets is not None:
                # Save the list of tweets to that user's document in the database
                output_collection.update_many({'id_str': user}, {'$set': {'tweets': tweets}})


def process_followers(users, output_collection, api):
    # For each user
    for user in users:
        # If there is not already a document for that user that has followers
        if output_collection.count_documents({'id_str': user, 'follower_ids': {'$exists': True}}) < 1:
            print(f"Downloading followers for ${user}")
            # Download the list of the user's followers
            follower_ids = download_follower_ids(api, user)
            if follower_ids is not None:
                # Save the list of followers to that user's document in the database
                output_collection.update_many({'id_str': user}, {'$set': {'follower_ids': follower_ids}})


def process_following(users, output_collection, api):
    # For each user
    for user in users:
        # If there is not already a document for that user that has their following
        if output_collection.count_documents({'id_str': user, 'following_ids': {'$exists': True}}) < 1:
            print(f"Downloading following for ${user}")
            # Download the list of the user's following
            following_ids = download_following_ids(api, user)
            if following_ids is not None:
                # Save the list of following to that user's document in the database
                output_collection.update_many({'id_str': user}, {'$set': {'following_ids': following_ids}})


def process_profile(users, output_collection, api):
    # For each user
    for user in users:
        # If there is not already a document for that user that has their profile information
        if output_collection.count_documents({'id_str': user, 'screen_name': {'$exists': True}}) < 1:
            print(f"Downloading profile for ${user}")
            # Download the user's profile
            profile = download_profile(api, user)
            if profile is not None:
                # Update the user's document with profile information
                output_collection.update_many({'id_str': user}, {'$set': profile})


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
