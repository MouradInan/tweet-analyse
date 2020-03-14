from flask import Flask
import tweepy
from flask import render_template
import json
import re
from stop_words import get_stop_words
from collections import Counter
from config import config
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules


app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')

def get_tweets(search):
    auth = tweepy.OAuthHandler(config.consume_key, config.consume_pkey)
    auth.set_access_token(config.access_key, config.access_pkey)

    api = tweepy.API(auth)

    search = api.search(search, count=200, result_type='recent', tweet_mode='extended', lang='fr')
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

    return results


@app.route('/get_tweets/<search>')
def word_cloud(search):
    results = get_tweets(search)
    test = []
    for text in results:
        splitted = text.split()
        test.append(splitted)
    words = []
    for splitted in test:
        for s in splitted:
            if s not in get_stop_words('fr') and len(s) > 3:
                words.append(s)
    words = [x.lower() for x in words]
    words = filter(lambda x: x != 'france' and x != 'électricité', words)
    counter = Counter(words)
    counter = counter.most_common()[:100]
    counter = [{'text': key, 'size': value} for key, value in counter]

    return json.dumps(counter, ensure_ascii=False)


@app.route('/association-rule/<search>')
def association_rule(search):
    results = get_tweets(search)
    results = [x.lower() for x in results]
    test = []
    for text in results:
        splitted = text.split()
        test.append(splitted)
    final = []
    for splitted in test:
        words = []
        for s in splitted:
            if s not in get_stop_words('fr') and len(s) > 3:
                words.append(s)
        final.append(words)
    df = pd.DataFrame(final)
    ohe_df = custom(df)
    freq_items = apriori(ohe_df, min_support=0.05, use_colnames=True, verbose=1)
    print(freq_items.sort_values(by='support', ascending=False).head(5))

    rules = association_rules(freq_items, metric="confidence", min_threshold=0.6)
    print(rules)
    to_show = rules[['antecedents', 'support', 'confidence', 'consequents']]
    return json.dumps(to_show.to_json(orient='records'), ensure_ascii=False)


def custom(df):
    encoded_vals = []
    items = (df[df.columns[0]].unique())
    for index, row in df.iterrows():
        labels = {}
        uncommons = list(set(items) - set(row))
        commons = list(set(items).intersection(row))
        for uc in uncommons:
            labels[uc] = 0
        for com in commons:
            labels[com] = 1
        encoded_vals.append(labels)
    ohe_df = pd.DataFrame(encoded_vals)
    return ohe_df
