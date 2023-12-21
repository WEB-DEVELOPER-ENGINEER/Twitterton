import os
import sys
import json

from .src.tweet_builder import get_tweet
from requests_oauthlib import OAuth1Session
import os
import json
import logging
import argparse
from dotenv import load_dotenv

logger = logging.getLogger("tweet")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

if os.path.exists("tweet_history.json"):
    try:
        with open("tweet_history.json", "r", encoding="utf-8") as tweet_history_file:
            json.load(tweet_history_file)
    except json.decoder.JSONDecodeError:
        with open("tweet_history.json", "w", encoding="utf-8") as tweet_history_file:
            tweet_history_file.write("[]")
else:
    with open("tweet_history.json", "w+", encoding="utf-8") as tweet_history_file:
        tweet_history_file.write("[]")

if not os.path.exists("idea_bank"):
    os.makedirs("idea_bank")


def setup_oauth():
    '''
    Setup OAuth1 authentication with Twitter.
    '''
    load_dotenv()

    consumer_key = os.getenv("CONSUMER_KEY")
    consumer_secret = os.getenv("CONSUMER_SECRET")
    access_token = os.getenv("ACCESS_TOKEN")
    access_token_secret = os.getenv("ACCESS_SECRET")

    return OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )


def post_tweet(oauth, payload):
    '''
    Post a tweet to Twitter.
    '''
    response = oauth.post(
        "https://api.twitter.com/2/tweets",
        json=payload,
    )

    if response.status_code not in [200, 201]:
        raise Exception(
            f"Request returned an error: {response.status_code} {response.text}"
        )

    print(f"Response code: {response.status_code}")
    print(json.dumps(response.json(), indent=4, sort_keys=True))


def main(promp, OPEN_AI_KEY, live=False):
    '''
    Generate a tweet and post it to Twitter.
    '''
    try:
        tweet = get_tweet(promp, OPEN_AI_KEY)
        if live:
            logger.info("Live mode. The tweet will be posted to Twitter.")
            oauth = setup_oauth()
            payload = {"text": tweet}
            post_tweet(oauth, payload)
        else:
            logger.info("Test mode. The tweet will was not be posted.")
            return(tweet)
    except Exception as err:
        raise err


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Post tweets to Twitter.')
    parser.add_argument('--live', action='store_true',
                        help='If set, the tweet will be posted to Twitter. Otherwise, the tweet will be printed to the console.')

    args = parser.parse_args()

    main(args.live)