# Twitter Keyword Search Tool

This script searches for keywords used in the last 7 days on Twitter, and saves the search result to MongoDB.
It will also provide functionality to download the histories of the users returned in the search.

## Usage

Execute `python -m twitterkeywordsearch` to run the script.

The script can be run in a variety of modes depending on what data should be collected.
These modes are `search` and `users`.
The mode is specified as a positional argument to the script.

The script requires the packages `tweepy`, `pymongo`, and `python-dotenv`.

### Search Mode

The `search` mode searches for recent tweets with a set of keywords/phrases.
The keywords are listed in a text file, with one phrase on each line.
The path to this file is specified by the `-q` argument.
These keywords are surrounded by quotes and joined by the `OR` operator in the final query sent to Twitter.

Tweets collected in this mode will be saved to a MongoDB collection specified by the `-o` argument.

The search will continue until either all results are hit, or a target number of results is found.
This target can be specified by a `-t` argument.

The script can also be configured to search for popular, recent, or a mix of tweets.
This can be specified by the `-s` argument.

### Users Mode

The `users` mode downloads information on the users discovered by the search mode.
This includes their profile, list of followed and following accounts, and most recent ~3000 Tweets.

It requires the `-i` parameter to specify the collection where searched tweets were saved.

The `-o` parameter again specifies the collection to save the user information to.

This mode will skip over users who already have information saved to the output collection.
This features allows for the process to recover after an error, power outage, etc.

Some limits can be provided to decrease the time required to download user information.
The number of follower and following IDs can be limited with the `-f1` and `-f2` arguments respectively.
This prevents the script from hanging on users with an outsized number of followers or following accounts.

## Environment Configuration

This script requires a .env file in the working directory with the following data:

```
TWITTER_API_KEY=<>
TWITTER_API_SECRET=<>
TWITTER_ACCESS_TOKEN=<>
TWITTER_TOKEN_SECRET=<>
DATABASE_URL=<>
```
