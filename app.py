from flask import Flask, flash, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import json
import tools
from datetime import datetime
import cleaner

database_uri = "mysql+pymysql://armin:armin@localhost/uni"
UPLOAD_FOLDER = '/tmp'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/store-file-to-sql', methods=['GET', 'POST'])
def store_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            create_tweets_table()
            tmp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'tmp-data-file')
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            file.save(tmp_path)
            return inject(tmp_path)
    else:
        return render_template('upload_file.html')


class RawTweet(db.Model):
    text = db.Column(db.String(400), nullable=False)
    tags = db.Column(db.Integer, nullable=False)
    id = db.Column(db.Integer, primary_key=True)

    def to_dict(self):
        return {
            'text': self.text,
            'tags': self.tags,
            'id': self.id
        }


class CleanStemmingTweet(db.Model):
    text = db.Column(db.String(400), nullable=False)
    id = db.Column(db.Integer, primary_key=True)

    def to_dict(self):
        return {
            'text': self.text,
            'id': self.id
        }


class CleanLemmatizerTweet(db.Model):
    text = db.Column(db.String(400), nullable=False)
    id = db.Column(db.Integer, primary_key=True)

    def to_dict(self):
        return {
            'text': self.text,
            'id': self.id
        }


class Emotion(db.Model):
    type = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer, primary_key=True)
    joy = db.Column(db.Float, nullable=False)
    fear = db.Column(db.Float, nullable=False)
    sadness = db.Column(db.Float, nullable=False)
    anger = db.Column(db.Float, nullable=False)
    surprise = db.Column(db.Float, nullable=False)
    disgust = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'joy': self.joy,
            'fear': self.fear,
            'sadness': self.sadness,
            'anger': self.anger,
            'surprise': self.surprise,
            'disgust': self.disgust
        }


def create_tweets_table():
    db.create_all()


def inject(path):
    progress = 0
    with open(path) as f:
        line = f.readline()
        while line:
            content = json.loads('[' + line + ']')
            for tweet in content:
                if 'data' in tweet.keys():
                    text = tweet['data']['text']
                    tags = []
                    for rule in tweet['matching_rules']:
                        tags.append(rule['tag'].strip('-vip'))
                    tags = set(tags)
                db.session.merge(RawTweet(text=text, tags=tools.convert_tags_to_int(tags)))
            progress += 1
            if progress % 10000 == 0:
                print(progress)
            line = f.readline()
    db.session.commit()
    return "Read and Store {} tweets from uploaded file!".format(progress)


@app.route('/raw_emotion')
def raw_emotion_calculation():
    create_tweets_table()
    raw_tweets = list(tweets.to_dict() for tweets in RawTweet.query.all())
    start = datetime.timestamp(datetime.now())
    for raw_tweet in raw_tweets:
        emotions = tools.emotion_detector([raw_tweet['text']]).values.tolist()[0]
        db.session.merge(Emotion(
                type=0,
                id=raw_tweet['id'],
                anger=emotions[1],
                disgust=emotions[2],
                fear=emotions[3],
                joy=emotions[4],
                sadness=emotions[5],
                surprise=emotions[6]
            ))
    print(datetime.timestamp(datetime.now()) - start)
    db.session.commit()
    return "Emotion calculated for raw tweets!"


@app.route('/stemming_emotion')
def stemming_emotion_calculation():
    create_tweets_table()
    # TODO insert emotion for stemming tweets
    # stemming_tweets = list(tweets.to_dict() for tweets in CleanStemmingTweet.query.all())
    return ""


@app.route('/lemmatize_emotion')
def lemmatize_emotion_calculation():
    create_tweets_table()
    # TODO insert emotion for lemmatize tweets
    # lemmatize_tweets = list(tweets.to_dict() for tweets in CleanLemmatizerTweet.query.all())
    return ""


@app.route('/clean')
def cleaning_tweets():
    create_tweets_table()
    tweets = RawTweet.query.all()
    # TODO
    # clean_tweets = cleaner.clean(list(tweets.to_dict() for tweets in RawTweet.query.all()))
    return ""


if __name__ == '__main__':
    app.run()
