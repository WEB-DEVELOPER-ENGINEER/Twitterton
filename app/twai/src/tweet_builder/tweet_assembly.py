import os
import sys
import json
import logging
import openai
from .tweet_concept import generate_concept

logger = logging.getLogger("tweet_builder")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


def validate_tweet(tweet_text):
    if len(tweet_text) > 280:
        logger.error("Tweet is too long. Tweet length: %i", len(tweet_text))
        return False
    return tweet_text


def get_tweet( promp, OPEN_AI_KEY, max_attempts=10):
    '''
    Returns a tweet that is less than 280 characters.
    '''
    openai.api_key = OPEN_AI_KEY
    attempts = 0
    while attempts < max_attempts:
        logger.info("Attempt %i of %i to generate a tweet.",
                    attempts + 1, max_attempts)
        logger.info("Generating tweet...")
        tweet, _ = generate_concept(promp, OPEN_AI_KEY)
        logger.debug("Tweet: %s", tweet)
        logger.info("Validating tweet...")
        if validate_tweet(tweet):
            with open("tweet_history.json", "r", encoding="UTF-8") as tweet_history_file:
                tweet_history = json.load(tweet_history_file)
            tweet_history.append(tweet)
            with open("tweet_history.json", "w", encoding="UTF-8") as tweet_history_file:
                json.dump(tweet_history, tweet_history_file, indent=4)
            return tweet
        else:
            attempts += 1
    raise ValueError("Unable to create a tweet within the character limit after 10 attempts.")