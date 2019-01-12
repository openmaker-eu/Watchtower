import sys
from time import gmtime, strftime, time
import datetime
from decouple import config
from nltk.corpus import stopwords

sys.path.insert(0, config("ROOT_DIR"))

from application.Connections import Connection

stops_1 = ['i', '', '-', '&amp;', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't", 'days', 'day']

stops_2 = stopwords.words('english')

stops = list(stops_1 + stops_2)

def getDateWords(alertid, date):
    return list(Connection.Instance().db[str(alertid)].aggregate([
        {
            '$match': {
                'timestamp_ms': {'$gte': str(date)}
            }
        },
        {
            '$project': {
                'text': {
                    '$split': [
                        {
                            '$toLower': '$extended_tweet.full_text'
                        }, ' '
                    ]
                }
            }
        },
        {
            '$unwind': '$text'
        },
        {
            '$project' : {
                'text': '$text',
                'text_len': {'$strLenCP': "$text" },
            }
        },
        {
            '$match': {
               'text': { '$nin': stops },
               'text_len': { '$gt': 1 }
            }
        },
        {
            '$group': {
                '_id': '$text',
                'count': { '$sum': 1 }
            }
        },
        {
            '$project' : {
                'word' : '$_id',
                'count' : '$count',
                '_id' : 0
            }
        },
        {
            '$sort': {'count': -1}
        },
        {'$limit': 50}
    ]))



def calc(alertid):
    current_milli_time = int(round(time() * 1000))
    one_day = 86400000

    result = {
        'words': getDateWords(alertid, current_milli_time - one_day),
        'modified_date': datetime.datetime.now()
    }

    Connection.Instance().daily_words[str(alertid)].insert_one(result)


if __name__ == '__main__':
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id "
            "FROM topics"
        )
        cur.execute(sql)
        alert_list = cur.fetchall()
        for alert in alert_list:
            print(alert[0])
            calc(alert[0])
