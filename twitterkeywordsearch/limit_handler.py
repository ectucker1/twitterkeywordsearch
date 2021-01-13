import tweepy
import time


# Iterates over the pages in the cursor and sleeps if the rate limit is hit
def limit_handled(cursor):
    finished = False
    while not finished:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            print('Rate limit hit. Sleeping for 15 minutes.')
            time.sleep(15 * 60)
        except StopIteration:
            finished = True
