import nltk
import string
import re


def clean(raw_tweets):
    # for tweet in raw_tweets:
    #     print(tweet['text'])
    print(clean_text_with_stemming(raw_tweets[0]['text']))
    print(clean_text_with_lemmatizer(raw_tweets[0]['text']))


def clean_text_with_stemming(text):
    text_lc = "".join([word.lower() for word in text if word not in string.punctuation])
    text_rc = re.sub('[0-9]+', '', text_lc)
    tokens = re.split('\W+', text_rc)
    stopword = nltk.corpus.stopwords.words('english')
    ps = nltk.PorterStemmer()
    text = [ps.stem(word) for word in tokens if word not in stopword]
    return text


def clean_text_with_lemmatizer(text):
    text_lc = "".join([word.lower() for word in text if word not in string.punctuation])
    text_rc = re.sub('[0-9]+', '', text_lc)
    tokens = re.split('\W+', text_rc)
    stopword = nltk.corpus.stopwords.words('english')
    wn = nltk.WordNetLemmatizer()
    text = [wn.lemmatize(word) for word in tokens if word not in stopword]
    return text
