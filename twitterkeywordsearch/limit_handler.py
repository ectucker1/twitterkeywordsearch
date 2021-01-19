import tweepy
import time


# Call given function, but sleep if the rate limit is hit
def limit_handled(fun, **kwargs):
    try:
        return fun(**kwargs)
    except tweepy.RateLimitError:
        print("Rate limit hit. Sleeping for 15 minutes")
        time.sleep(15 * 60)
        return limit_handled(fun, **kwargs)
