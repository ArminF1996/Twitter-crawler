import pandas as pd
from flask_sqlalchemy import sqlalchemy as sql
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, recall_score, precision_score, f1_score
import string

import app

database_uri = "mysql+pymysql://armin:armin@localhost/uni?charset=utf8mb4"
engine = sql.create_engine(database_uri)


def run(query):
    sql_query = pd.read_sql_query(query, engine)
    df = pd.DataFrame(sql_query, columns=['type', 'id', 'text', 'candidate'])
    df['text'] = df.text.map(lambda x: x.lower().translate(str.maketrans('', '', string.punctuation)))
    type_train, type_test, id_train, id_test, text_train, text_test, candidate_train, candidate_test = train_test_split(
        df['type'],
        df['id'],
        df['text'],
        df['candidate'],
        test_size=0.8,
        random_state=1
    )
    count_vector = CountVectorizer(stop_words='english')
    training_data = count_vector.fit_transform(text_train)
    testing_data = count_vector.transform(text_test)
    naive_bayes = MultinomialNB()
    naive_bayes.fit(training_data, candidate_train)
    predictions = naive_bayes.predict(testing_data)

    result = []
    type_test_arr = type_test.values.tolist()
    type_train_arr = type_test.values.tolist()
    id_test_arr = id_test.values.tolist()
    id_train_arr = id_train.values.tolist()
    tag_train_arr = candidate_train.values.tolist()
    for i in range(len(id_train)):
        result.append(app.Bayes(type=type_train_arr[i],
                                id=id_train_arr[i],
                                tag=tag_train_arr[i]))
    for i in range(len(id_test)):
        result.append(app.Bayes(type=type_test_arr[i],
                                id=id_test_arr[i],
                                tag=predictions[i]))

    print("Training dataset: ", candidate_train.shape[0])
    print("Test dataset: ", candidate_test.shape[0])
    print("Accuracy score: ", accuracy_score(candidate_test, predictions))
    return result

