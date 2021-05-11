from flask import Flask, flash, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
import os
import json
import naive_bayes
import tools
import demoji
from datetime import datetime
from emotion_predictor import EmotionPredictor
import copy

model = EmotionPredictor(classification='ekman', setting='mc')

database_uri = "mysql+pymysql://armin:armin@localhost/uni?charset=utf8mb4"
UPLOAD_FOLDER = '/tmp'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

key_words = [["corona", "covid19"], ["gdp", "economy", "industry"], ["unemployment", "job", "income"],
             ["china", "tradewar", "chinese"], ["election"], ["race", "racism", "blacklivesmatter"]]
demoji.download_codes()
tags_variety = ['corona', 'economy', 'job', 'china', 'election', 'race']

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


class TFIDF(db.Model):
    type = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer, primary_key=True)
    corona = db.Column(db.Float, nullable=False)
    economy = db.Column(db.Float, nullable=False)
    job = db.Column(db.Float, nullable=False)
    china = db.Column(db.Float, nullable=False)
    election = db.Column(db.Float, nullable=False)
    race = db.Column(db.Float, nullable=False)
    candidate = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'corona': self.corona,
            'economy': self.economy,
            'job': self.job,
            'china': self.china,
            'election': self.election,
            'race': self.race,
            'candidate': self.candidate
        }


class Bayes(db.Model):
    type = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'tag': self.tag
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
                    text = demoji.replace(tweet['data']['text'], " ")
                    text = " ".join(filter(lambda x: x[0] != '@', text.lower().split()))
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


@app.route('/emotion/raw/<start>/<end>')
def raw_emotion_calculation(start=None, end=None):
    create_tweets_table()
    start_time = datetime.timestamp(datetime.now())
    raw_tweets = list(tweets.to_dict() for tweets in RawTweet.query
                      .filter(RawTweet.id >= start).filter(RawTweet.id <= end).all())
    emotion_detector(raw_tweets, 0)
    print(datetime.timestamp(datetime.now()) - start_time)
    return "Emotion calculated for raw tweets from id={} to id={}!".format(start, end)


@app.route('/emotion/stemming')
def stemming_emotion_calculation():
    create_tweets_table()
    stemming_tweets = list(tweets.to_dict() for tweets in CleanStemmingTweet.query.all())
    emotion_detector(stemming_tweets, 1)
    return "Emotion calculated for stemming tweets!"


@app.route('/emotion/lemmatize/<start>/<end>')
def lemmatize_emotion_calculation(start=None, end=None):
    create_tweets_table()
    lemmatize_tweets = list(tweets.to_dict() for tweets in CleanLemmatizerTweet.query
                            .filter(RawTweet.id >= start).filter(RawTweet.id <= end).all())
    emotion_detector(lemmatize_tweets, 2)
    return "Emotion calculated for lemmatize tweets from id={} to id={}!".format(start, end)


def emotion_detector(tweets, type_number):
    cnt = 0
    for tweet in tweets:
        emotions = model.predict_probabilities([tweet['text']]).values.tolist()[0]
        db.session.merge(Emotion(
            type=type_number,
            id=tweet['id'],
            anger=emotions[1],
            disgust=emotions[2],
            fear=emotions[3],
            joy=emotions[4],
            sadness=emotions[5],
            surprise=emotions[6]
        ))
        cnt += 1
        if cnt % 1000 == 0:
            print(cnt)
    db.session.commit()


@app.route('/clean/stemming')
def cleaning_tweets_with_stemming():
    create_tweets_table()
    tweets = list(tweets.to_dict() for tweets in RawTweet.query.all())
    for tweet in tweets:
        cleaned_text = " ".join(tools.clean_text_with_stemming(tweet['text']))
        db.session.merge(CleanStemmingTweet(text=cleaned_text, id=tweet['id']))
    db.session.commit()
    return "Tweets were cleaned with stemming method!"


@app.route('/clean/lemmatize/<start>/<end>')
def cleaning_tweets_with_lemmatize(start=None, end=None):
    create_tweets_table()
    tweets = list(tweets.to_dict() for tweets in RawTweet.query
                  .filter(RawTweet.id >= start).filter(RawTweet.id <= end).all())
    for tweet in tweets:
        cleaned_text = " ".join(tools.clean_text_with_lemmatizer(tweet['text']))
        db.session.merge(CleanLemmatizerTweet(text=cleaned_text, id=tweet['id']))
    db.session.commit()
    return "Tweets were cleaned with lemmatize method from id={} to id={}!".format(start, end)


@app.route('/tfidf/raw')
def calculate_tfidf_raw():
    create_tweets_table()
    tweets = list(tweets.to_dict() for tweets in RawTweet.query.all())
    total = [0] * 6
    rows, cols = (len(tweets), 6)
    arr = [[0] * cols] * rows

    for tweet in tweets:
        text = tweet['text']
        cur = tweet['id'] - 1
        arr[cur] = [0, 0, 0, 0, 0, 0]
        for i in range(6):
            for key_word in key_words[i]:
                arr[cur][i] += text.count(key_word)
            total[i] += arr[cur][i]

    for i in range(rows):
        for j in range(6):
            arr[i][j] = float(arr[i][j]) / total[j]
        max_index = arr[i].index(max(arr[i]))
        db.session.merge(
            TFIDF(id=i + 1,
                  type=0,
                  corona=arr[i][0],
                  economy=arr[i][1],
                  job=arr[i][2],
                  china=arr[i][3],
                  election=arr[i][4],
                  race=arr[i][5],
                  candidate=max_index,
                  ))
    db.session.commit()
    return "TF-IDF calculated for raw tweets!"


@app.route('/tfidf/stemming')
def calculate_tfidf_stemming():
    create_tweets_table()
    tweets = list(tweets.to_dict() for tweets in CleanStemmingTweet.query.all())
    total = [0] * 6
    rows, cols = (len(tweets), 6)
    arr = [[0] * cols] * rows

    for tweet in tweets:
        text = tweet['text']
        cur = tweet['id'] - 1
        arr[cur] = [0, 0, 0, 0, 0, 0]
        for i in range(6):
            for key_word in key_words[i]:
                arr[cur][i] += text.count(key_word)
            total[i] += arr[cur][i]

    for i in range(rows):
        for j in range(6):
            arr[i][j] = float(arr[i][j]) / total[j]
        max_index = arr[i].index(max(arr[i]))
        db.session.merge(
            TFIDF(id=i + 1,
                  type=1,
                  corona=arr[i][0],
                  economy=arr[i][1],
                  job=arr[i][2],
                  china=arr[i][3],
                  election=arr[i][4],
                  race=arr[i][5],
                  candidate=max_index,
                  ))
    db.session.commit()
    return "TF-IDF calculated for stemming tweets!"


@app.route('/tfidf/lemmatize')
def calculate_tfidf_lemmatize():
    create_tweets_table()
    tweets = list(tweets.to_dict() for tweets in CleanLemmatizerTweet.query.all())
    total = [0] * 6
    rows, cols = (len(tweets), 6)
    arr = [[0] * cols] * rows

    for tweet in tweets:
        text = tweet['text']
        cur = tweet['id'] - 1
        arr[cur] = [0, 0, 0, 0, 0, 0]
        for i in range(6):
            for key_word in key_words[i]:
                arr[cur][i] += text.count(key_word)
            total[i] += arr[cur][i]

    for i in range(rows):
        for j in range(6):
            arr[i][j] = float(arr[i][j]) / total[j]
        max_index = arr[i].index(max(arr[i]))
        db.session.merge(
            TFIDF(id=i + 1,
                  type=2,
                  corona=arr[i][0],
                  economy=arr[i][1],
                  job=arr[i][2],
                  china=arr[i][3],
                  election=arr[i][4],
                  race=arr[i][5],
                  candidate=max_index,
                  ))
    db.session.commit()
    return "TF-IDF calculated for lemmatize tweets!"


@app.route('/bayes/raw')
def calculate_bayes_raw():
    create_tweets_table()
    query = '''SELECT type, TFIDF.id, text, candidate FROM raw_tweet INNER JOIN TFIDF ON raw_tweet.id=TFIDF.id AND type=0'''
    entities = naive_bayes.run(query)
    tmp = 0
    print(datetime.timestamp(datetime.now()))
    for entity in entities:
        db.session.merge(entity)
        tmp += 1
        if tmp % 10000 == 0:
            print(tmp)
            print(datetime.timestamp(datetime.now()))
    db.session.commit()
    return "naive bayes calculated for raw tweets!"


@app.route('/bayes/stemming')
def calculate_bayes_stemming():
    create_tweets_table()
    query = '''SELECT type, TFIDF.id, text, candidate FROM raw_tweet INNER JOIN TFIDF ON raw_tweet.id=TFIDF.id AND type=1'''
    entities = naive_bayes.run(query)
    for entity in entities:
        db.session.merge(entity)
    db.session.commit()
    return "naive bayes calculated for raw tweets!"


@app.route('/bayes/lemmatize')
def calculate_bayes_lemmatize():
    create_tweets_table()
    query = '''SELECT type, TFIDF.id, text, candidate FROM raw_tweet INNER JOIN TFIDF ON raw_tweet.id=TFIDF.id AND type=2'''
    entities = naive_bayes.run(query)
    for entity in entities:
        db.session.merge(entity)
    db.session.commit()
    return "naive bayes calculated for raw tweets!"


tmp = {'joy': 0, 'fear': 0, 'sadness': 0, 'anger': 0, 'surprise': 0, 'disgust': 0}


@app.route('/analyse/raw/bayes/<limit>')
def analyse_raw_bayes(limit):
    tags = list(bayes.to_dict() for bayes in Bayes.query.filter(Bayes.type == 0).filter(Bayes.id <= limit).all())
    emotions = list(emotion.to_dict() for emotion in Emotion.query.filter(Emotion.type == 0).filter(Emotion.id <= limit).all())
    result = {'corona': copy.deepcopy(tmp), 'economy': copy.deepcopy(tmp), 'job': copy.deepcopy(tmp),
              'china': copy.deepcopy(tmp), 'election': copy.deepcopy(tmp), 'race': copy.deepcopy(tmp)}

    cnt = 0
    for cnt in range(len(tags)):
        result[tags_variety[tags[cnt]['tag']]]['joy'] += emotions[cnt]['joy']
        result[tags_variety[tags[cnt]['tag']]]['fear'] += emotions[cnt]['fear']
        result[tags_variety[tags[cnt]['tag']]]['sadness'] += emotions[cnt]['sadness']
        result[tags_variety[tags[cnt]['tag']]]['anger'] += emotions[cnt]['anger']
        result[tags_variety[tags[cnt]['tag']]]['surprise'] += emotions[cnt]['surprise']
        result[tags_variety[tags[cnt]['tag']]]['disgust'] += emotions[cnt]['disgust']
        cnt += 1
    return json.dumps(result)


@app.route('/analyse/raw/tfidf/<limit>')
def analyse_raw_tfidf(limit):
    tags = list(tfidf.to_dict() for tfidf in TFIDF.query.filter(TFIDF.type == 0).filter(TFIDF.id <= limit).all())
    emotions = list(
        emotion.to_dict() for emotion in Emotion.query.filter(Emotion.type == 0).filter(Emotion.id <= limit).all())
    result = {'corona': copy.deepcopy(tmp), 'economy': copy.deepcopy(tmp), 'job': copy.deepcopy(tmp),
              'china': copy.deepcopy(tmp), 'election': copy.deepcopy(tmp), 'race': copy.deepcopy(tmp)}
    cnt = 0
    for cnt in range(len(tags)):
        for tmp_tag in tags_variety:
            result[tmp_tag]['joy'] += emotions[cnt]['joy'] * tags[cnt][tmp_tag]
            result[tmp_tag]['fear'] += emotions[cnt]['fear'] * tags[cnt][tmp_tag]
            result[tmp_tag]['sadness'] += emotions[cnt]['sadness'] * tags[cnt][tmp_tag]
            result[tmp_tag]['anger'] += emotions[cnt]['anger'] * tags[cnt][tmp_tag]
            result[tmp_tag]['surprise'] += emotions[cnt]['surprise'] * tags[cnt][tmp_tag]
            result[tmp_tag]['disgust'] += emotions[cnt]['disgust'] * tags[cnt][tmp_tag]
        cnt += 1
    return json.dumps(result)


@app.route('/analyse/lemmatize/bayes/<limit>')
def analyse_lemmatize_bayes(limit):
    tags = list(bayes.to_dict() for bayes in Bayes.query.filter(Bayes.type == 2).filter(Bayes.id <= limit).all())
    emotions = list(
        emotion.to_dict() for emotion in Emotion.query.filter(Emotion.type == 2).filter(Emotion.id <= limit).all())
    result = {'corona': copy.deepcopy(tmp), 'economy': copy.deepcopy(tmp), 'job': copy.deepcopy(tmp),
              'china': copy.deepcopy(tmp), 'election': copy.deepcopy(tmp), 'race': copy.deepcopy(tmp)}

    cnt = 0
    for cnt in range(len(tags)):
        result[tags_variety[tags[cnt]['tag']]]['joy'] += emotions[cnt]['joy']
        result[tags_variety[tags[cnt]['tag']]]['fear'] += emotions[cnt]['fear']
        result[tags_variety[tags[cnt]['tag']]]['sadness'] += emotions[cnt]['sadness']
        result[tags_variety[tags[cnt]['tag']]]['anger'] += emotions[cnt]['anger']
        result[tags_variety[tags[cnt]['tag']]]['surprise'] += emotions[cnt]['surprise']
        result[tags_variety[tags[cnt]['tag']]]['disgust'] += emotions[cnt]['disgust']
        cnt += 1
    return json.dumps(result)


@app.route('/analyse/lemmatize/tfidf/<limit>')
def analyse_lemmatize_tfidf(limit):
    tags = list(tfidf.to_dict() for tfidf in TFIDF.query.filter(TFIDF.type == 0).filter(TFIDF.id <= limit).all())
    emotions = list(
        emotion.to_dict() for emotion in Emotion.query.filter(Emotion.type == 0).filter(Emotion.id <= limit).all())
    result = {'corona': copy.deepcopy(tmp), 'economy': copy.deepcopy(tmp), 'job': copy.deepcopy(tmp),
              'china': copy.deepcopy(tmp), 'election': copy.deepcopy(tmp), 'race': copy.deepcopy(tmp)}
    cnt = 0
    for cnt in range(len(tags)):
        for tmp_tag in tags_variety:
            result[tmp_tag]['joy'] += emotions[cnt]['joy'] * tags[cnt][tmp_tag]
            result[tmp_tag]['fear'] += emotions[cnt]['fear'] * tags[cnt][tmp_tag]
            result[tmp_tag]['sadness'] += emotions[cnt]['sadness'] * tags[cnt][tmp_tag]
            result[tmp_tag]['anger'] += emotions[cnt]['anger'] * tags[cnt][tmp_tag]
            result[tmp_tag]['surprise'] += emotions[cnt]['surprise'] * tags[cnt][tmp_tag]
            result[tmp_tag]['disgust'] += emotions[cnt]['disgust'] * tags[cnt][tmp_tag]
        cnt += 1
    return json.dumps(result)


if __name__ == '__main__':
    app.run()
