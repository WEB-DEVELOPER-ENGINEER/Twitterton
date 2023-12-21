import tweepy
import logging
from datetime import datetime, timedelta
from app.main import Tweet, app, db
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INTERVAL = 60
DEBUG = True

def main():
    while True:
        with app.app_context():
            tweet_records = Tweet.query.all()
            cur_time = datetime.utcnow() + timedelta(hours=2, minutes=0)
            logger.info(f'{len(tweet_records)} tweets found at {cur_time.time()}')
            for tweet in tweet_records:
                content = tweet.content
                date_time_obj = tweet.time
                status = tweet.status
                if status:
                    db.session.delete(tweet)
                    db.session.commit()
                else:
                    c_time = datetime.utcnow() + timedelta(hours=2, minutes=0)
                    if date_time_obj < c_time:
                        try:
                            client = tweepy.Client(
                            consumer_key=tweet.consumer_key,
                            consumer_secret=tweet.consumer_secret,
                            access_token=tweet.access_token,
                            access_token_secret=tweet.access_secret
                            )
                            client.create_tweet(text=content)
                            tweet.status = True
                            db.session.commit()
                        except Exception as e:
                            logger.warning(f'Exception during tweet! {e}')
        time.sleep(INTERVAL)

if __name__ == '__main__':
    main()
