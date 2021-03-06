import tweepy
from twitterkeywordsearch.data_transform import transform_status, transform_user
from twitterkeywordsearch.limit_handler import limit_handled


# Downloads the bio and other profile information of a given user
def download_profile(api, id):
    # Wrap calls to Twitter in try-except
    try:
        # Download the basic profile information of the user
        profile = limit_handled(api.get_user, id=id)
        profile = transform_user(profile._json)

        return profile
    # If there is an error in downloading, return None
    except tweepy.TweepError as ex:
        if "Not authorized" in ex.reason:
            print(f"User {id} has been deleted, suspended, or has a protected profile")
        else:
            print(ex)
        return None


# Return a list of all accounts following a given user
def download_follower_ids(api, id, max):
    try:
        # Download the ids of all accounts following this user
        follower_ids = []
        for page in tweepy.Cursor(api.followers_ids, id=id,
                                  monitor_rate_limit=True, wait_on_rate_limit=True, wait_on_rate_limit_notify=True,
                                  retry_count=5, retry_delay=5).pages():
            follower_ids = follower_ids + page
            # If more than the maximum number of follower accounts have been downloaded
            if len(follower_ids) >= max:
                # Stop downloading there
                break
        return follower_ids
    # If there is an error in downloading, return None
    except tweepy.TweepError as ex:
        if "Not authorized" in ex.reason:
            print(f"User {id} has been deleted, suspended, or has a protected profile")
        else:
            print(ex)
        return None


# Download a list of all accounts followed by a given user
def download_following_ids(api, id, max):
    try:
        # Download the ids of all accounts being followed
        following_ids = []
        for page in tweepy.Cursor(api.friends_ids, id=id,
                                  monitor_rate_limit=True, wait_on_rate_limit=True, wait_on_rate_limit_notify=True,
                                  retry_count=5, retry_delay=5).pages():
            following_ids = following_ids + page
            # If more than the maximum number of following accounts have been downloaded
            if len(following_ids) >= max:
                # Stop downloading there
                break
        return following_ids
    # If there is an error in downloading, return None
    except tweepy.TweepError as ex:
        if "Not authorized" in ex.reason:
            print(f"User {id} has been deleted, suspended, or has a protected profile")
        else:
            print(ex)
        return None


# Downloads the most recent 3200 tweets from the user
def download_tweets(api, id, last_year):
    # Wrap calls to Twitter in try-except
    try:
        # Download the user's most recent tweets
        tweets = []
        for page in tweepy.Cursor(api.user_timeline, id=id, tweet_mode="extended",
                                  monitor_rate_limit=True, wait_on_rate_limit=True, wait_on_rate_limit_notify=True,
                                  retry_count=5, retry_delay=5).pages():
            transformed = [transform_status(status._json) for status in page]
            tweets = tweets + transformed
            # If the last tweet is older than the target
            if tweets[-1]['created_at'].year < last_year:
                # Don't download any more tweets
                break

        # Return the list of tweets
        return tweets
    # If there is an error in downloading, return None
    except tweepy.TweepError as ex:
        if "Not authorized" in ex.reason:
            print(f"User {id} has been deleted, suspended, or has a protected profile")
        else:
            print(ex)
        return None


# Loads a list of user ids from a file
def load_user_list(path):
    users = set()
    # Open the file
    with open(path, 'r') as file:
        # For each line in the file
        for name in file:
            # Add that user ID to the list
            name = name.strip()
            if len(name) > 0:
                users.add(name)
    return users
