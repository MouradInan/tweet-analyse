from flask import Flask
import tweepy
from flask import render_template
import json
import re
from stop_words import get_stop_words
from collections import Counter
from config import config

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_tweets')
def hello_world():
    auth = tweepy.OAuthHandler(config.consume_key, config.consume_pkey)
    auth.set_access_token(config.access_key, config.access_pkey)

    api = tweepy.API(auth)

    search = api.search('électricité de france', count=200, result_type='recent', tweet_mode='extended')
    results = []
    for tweet in search:
        if 'retweeted_status' in dir(tweet):
            text = re.sub(r'@\w*', '', tweet.retweeted_status.full_text)
            text = re.sub(r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?', '', text)
            text = text.replace('\n', '')
            text = re.sub(r'[^\w\s]', ' ', text)

            results.append(text)
        else:
            text = re.sub(r'@\w*', '', tweet.full_text)
            text = re.sub(r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?', '', text)
            text = text.replace('\n', '')
            text = re.sub(r'[^\w\s]', ' ', text)

            results.append(text)
    words = []
    for text in results:
        splitted = text.split()
        for s in splitted:
            if s not in get_stop_words('fr') and len(s) > 3:
                words.append(s)

    words = [x.lower() for x in words]
    counter = Counter(words)
    counter = [{'text': key, 'size': value} for key, value in counter.items()]
    return json.dumps(counter, ensure_ascii=False)


