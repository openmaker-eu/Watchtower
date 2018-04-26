import urllib
import nltk
import json
from nltk.corpus import stopwords
from nltk.stem.porter import *
from time import gmtime, strftime, time
from decouple import config
from datetime import datetime, timezone
from dateutil import parser
import pymongo
import sys
sys.path.insert(0, config("ROOT_DIR"))
from application.Connections import Connection


blacklist = ["party", "erasmus", "deal", "discount"]
numOfTweets = 10
keyword_size = 10
timeThreshold = 12  # in months

def tokenize(text):
    stop_words = set(stopwords.words('english'))
    delimiters = ["<", ">", "#", "@", "“", "”", '.', "‘", '—', '"', ',',
                  "’", "'", '?', '!', ':', ';', '(', ')', '[', ']', '{', '}', '&',  "-"]
    extraStopWords = ['a', 'in', "--", "---", "the", "bi", "https"]
    stop_words.update(delimiters)
    stop_words.update(extraStopWords)
    tokens = nltk.word_tokenize(text)
    tokens = [i.lower().translate({ord(c): None for c in delimiters})
              for i in tokens if i.lower() not in stop_words]
    return tokens


def countOccurences(fullTextTokens, query):
    count = 0
    if query and fullTextTokens:
        # First try each word for equality
        for word in fullTextTokens:
            if word == query:
                count += 1
        # Word 2-gram
        for index in range(len(fullTextTokens) - 1):
            if (fullTextTokens[index] + fullTextTokens[index + 1]) == query:
                count += 1
    return count

def countKeywordsInTweet(fullTexts, queries):
    count = [0] * len(queries)
    for fullText in fullTexts:
        fullTextTokens = tokenize(fullText)
        for index, query in enumerate(queries):
            count[index] += countOccurences(fullTextTokens, query)
    return count

def fetchKeywords(topicID, keyword_size):
    urllink = "http://" + \
        config("HOST_IP") + ":8484/api/v1.3/get_hashtags?topic_id=" + str(topicID)
    with urllib.request.urlopen(urllink) as response:
        html = response.read().decode()
    hashtags = json.loads(html)["hashtags"]
    keywords = [(str(x["hashtag"]).lower() , int(x["count"])) for x in hashtags[:keyword_size]]

    if not keywords:
        return None

    # normalize count so that maximum of them is 10
    maxCount = max([x[1] for x in keywords])
    keywords = [(hashtag, max(int((count/maxCount)*10), 1) ) for hashtag,count in keywords]
    return keywords

def calculateScore(per, keywords):
    '''
    each word in blacklist -> -20 points
    if last tweet is outdated -> -50 points
    for each relevant keyword in hashtags -> +1 points

    final score = followers_count*(calculated_score)
    '''
    
    # inverse zip, divide into two seperate lists
    keywords, keywordCounts = zip(*keywords)

    penalty = -20*sum([word in per["description"] for word in blacklist])

    status_list = get_last_tweets(per["id"])

    if not status_list:
        return None

    last_tweet_outdated = (datetime.now(timezone.utc) - parser.parse(status_list[-1]["created_at"])).total_seconds() > timeThreshold * 30 * 24 * 60 * 60
    if last_tweet_outdated:
        penalty -= 50

    hashtags = set([str(x["text"]).lower() for y in status_list for x in y["entities"]["hashtags"]])
    hashtagCount = sum(y if x in hashtags else 0 for x,y in zip(keywords, keywordCounts))
    #hashtagCount = sum(keyword in hashtags for keyword in keywords)
    
    fullTexts = [x["full_text"] for x in status_list]
    keywordOccurenceNumbers = countKeywordsInTweet(fullTexts, keywords)
    count = sum([keywordOccurence*multiplier for keywordOccurence, multiplier in zip(keywordOccurenceNumbers, keywordCounts)])

    final_score = per["followers_count"]*(count + hashtagCount + penalty)

    return final_score

def get_last_tweets(twitter_id):
    resp = list(Connection.Instance().MongoDBClient.last_tweets["tweets"].find({"id" : twitter_id}))

    if resp:
        return resp[0]["tweets"]
    
    return None

def update_influencer_score():
    for collection_name in Connection.Instance().audience_samples_DB.collection_names():
        collection = Connection.Instance().audience_samples_DB[collection_name]
        start = time()
        print("Currently updating collection " + collection_name)
        topicID = int(collection_name.split("_")[1])
        keywords = fetchKeywords(topicID, keyword_size)

        if not keywords:
            print("!!!Error fetching keywords!!!")
            continue

        bulk = collection.initialize_unordered_bulk_op()
        
        # Calculate score every time
        cursor = collection.find()

        for record in cursor:
            bulk.find({'_id':record['_id']}).update({'$set' : {"influencer_score" : calculateScore(record,keywords)}})

        print("...Executing bulk operation")
        try:
            bulk.execute()
        except pymongo.errors.InvalidOperation as e:
            print("..."+str(e))

        end = time()
        print("...It took {} seconds".format(end - start))

def get_local_influencers():
    # Sort audience sample and and write top 20 to influencers database
    for collection_name in Connection.Instance().audience_samples_DB.collection_names():
        collection = Connection.Instance().audience_samples_DB[collection_name]
        influencers = list(collection.find({}).sort([("influencer_score" , -1)]).limit(20))
        location, topic = collection_name.split("_")
        local_influencers_collection = Connection.Instance().local_influencers_DB[topic+"_"+location]
        local_influencers_collection.drop()
        local_influencers_collection.insert_many(influencers)

if __name__ == "__main__":
    update_influencer_score()
    get_local_influencers()