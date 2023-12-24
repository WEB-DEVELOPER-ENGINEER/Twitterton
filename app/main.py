from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from .twai.tweet_assembly import get_tweet

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/tweetdb'
db = SQLAlchemy(app)

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(280), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Boolean, default=False)
    consumer_key = db.Column(db.String(255), nullable=False)
    consumer_secret = db.Column(db.String(255), nullable=False)
    access_token = db.Column(db.String(255), nullable=False)
    access_secret = db.Column(db.String(255), nullable=False)
    openai_api_key = db.Column(db.String(255), nullable=True)

def get_date_time(date_time_str):
    date_time_obj = None
    error_code = None
    try:
        date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        error_code = f'Error! {e}'
    if date_time_obj is not None:
        cur_time = datetime.utcnow() + timedelta(hours=2, minutes=0)
        if date_time_obj < cur_time:
            error_code = "Invalid time."    
    return date_time_obj, error_code

@app.route("/")
def tweet_list():
    tweets = Tweet.query.order_by(Tweet.time.desc()).all()
    n_open_tweets = Tweet.query.filter_by(status=False).count()
    return render_template('index.html', tweets=tweets, n_open_tweets=n_open_tweets)


@app.route("/tweet", methods=['POST'])
def add_tweet():
    content = request.form['content']
    time = request.form['time']
    consumer_key = request.form.get('CONSUMER_KEY')
    consumer_secret = request.form.get('CONSUMER_SECRET')
    access_token = request.form.get('ACCESS_TOKEN')
    access_secret = request.form.get('ACCESS_SECRET')
    if not (consumer_key and time and content and consumer_secret and access_token and access_secret):
        return "ERROR! Enter input to all fields."
    date_time_obj, error_code = get_date_time(time)
    if error_code is not None:
        return error_code
    new_tweet = Tweet(content=content, time=date_time_obj, status=False, consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_secret=access_secret)
    db.session.add(new_tweet)
    db.session.commit()
    return redirect('/')

@app.route("/ai-tweet", methods=['POST'])
def add_tweet_ByAi():
    content = request.form['ai_prompt']
    time = request.form['ai_time']
    consumer_key = request.form.get('CONSUMER_KEY')
    consumer_secret = request.form.get('CONSUMER_SECRET')
    access_token = request.form.get('ACCESS_TOKEN')
    access_secret = request.form.get('ACCESS_SECRET')
    openai_api_key = request.form.get('OPENAI_API_KEY')
    if not (consumer_key and time and content and consumer_secret and access_token and access_secret and openai_api_key):
        return "ERROR! Enter input to all fields."
    date_time_obj, error_code = get_date_time(time)
    if error_code is not None:
        return error_code
    tweet = get_tweet(content, openai_api_key)
    new_tweet = Tweet(content=tweet, time=date_time_obj, status=False, consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_secret=access_secret, openai_api_key=openai_api_key)
    db.session.add(new_tweet)
    db.session.commit()
    return redirect('/')

@app.route("/delete/<int:tweet_id>")
def delete_tweet(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    db.session.delete(tweet)
    db.session.commit()
    return redirect('/')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
