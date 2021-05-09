import nltk
import string
import re
all_tags = {"corona": 0, "economy": 1, "job": 2, "china": 3, "election": 4, "race": 5}
nltk.download('stopwords')
nltk.download('wordnet')


def convert_tags_to_int(tags):
    int_value = 0
    for tag in tags:
        int_value += 2 ** all_tags.get(tag)
    return int_value


def convert_int_to_tags(int_value):
    tags = []
    for num in range(len(all_tags)):
        if (2 ** num) & int_value:
            tags.append(list(all_tags.keys())[num])
    return tags


def find_first_tag(int_value):
    for num in range(len(all_tags)):
        if (2 ** num) & int_value:
            return num


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
