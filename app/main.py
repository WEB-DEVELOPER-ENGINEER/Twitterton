from flask import Flask, render_template, request, session, redirect, url_for, flash
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from .twai.tweet_assembly import get_tweet
from .form import RegisterForm, LoginForm
from .decorators import login_required
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/tweetdb'
app.config['SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(80))
    email = db.Column(db.String(35), unique=True)
    username = db.Column(db.String(25), unique=True)
    password = db.Column(db.String(60))
    is_author = db.Column(db.Boolean)
    tweets = db.relationship('Tweet', backref='author', lazy='dynamic')

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))
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
@login_required
def tweet_list():
    author = Author.query.filter_by(username=session['username']).first()
    tweets = Tweet.query.filter_by(author_id=author.id).order_by(Tweet.time.desc()).all()
    n_open_tweets = Tweet.query.filter_by(author_id=author.id).count()
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
    new_tweet = Tweet(content=content, author_id=Author.query.filter_by(username=session['username']).first().id, time=date_time_obj, status=False, consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_secret=access_secret)
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
    new_tweet = Tweet(content=tweet, author_id=Author.query.filter_by(username=session['username']).first().id, time=date_time_obj, status=False, consumer_key=consumer_key, consumer_secret=consumer_secret, access_token=access_token, access_secret=access_secret, openai_api_key=openai_api_key)
    db.session.add(new_tweet)
    db.session.commit()
    return redirect('/')

@app.route("/delete/<int:tweet_id>")
def delete_tweet(tweet_id):
    tweet = Tweet.query.get_or_404(tweet_id)
    db.session.delete(tweet)
    db.session.commit()
    return redirect('/')

@app.route('/login', methods=('GET', 'POST'))
def login():
    form = LoginForm()
    error = None
    if request.method == 'GET' and request.args.get('next'):
        session['next'] = request.args.get('next', None)
    if form.validate_on_submit():
        author = Author.query.filter_by(
            username=form.username.data,
            ).first()
        if author:
            if bcrypt.hashpw(form.password.data.encode('utf-8'), author.password.encode('utf-8')) == author.password.encode('utf-8'):
                session['username'] = form.username.data
                session['is_author'] = author.is_author
                flash("User %s logged in" % author.username)
                if 'next' in session:
                    next = session.get('next')
                    session.pop('next')
                    return redirect('/')
                else:
                    return redirect('/')
            else:
                error = "Incorrect password"
        else:
            error = "Author not found"
    return render_template('login.html', form=form, error=error)

@app.route('/register', methods=('GET', 'POST'))
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(form.password.data.encode('utf-8'), salt)
        author = Author(
            fullname=form.fullname.data,
            email=form.email.data,
            username=form.username.data,
            password=hashed_password,
            is_author=False
        )
        db.session.add(author)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html', form=form)

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username')
    session.pop('is_author')
    flash("User logged out")
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
