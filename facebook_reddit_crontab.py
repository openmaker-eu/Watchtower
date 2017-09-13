import re
import time
from datetime import datetime, timedelta

import facebook
import praw
import requests

import link_parser
from application.Connections import Connection


def mineFacebookConversations(search_ids, isPreview, timeFilter="day"):
    my_token = Connection.Instance().redditFacebookDB['tokens'].find_one()["facebook"]["token"]
    graph = facebook.GraphAPI(access_token=my_token, version="2.7")

    if timeFilter == "day":
        d = str(datetime.utcnow() - timedelta(hours=24))
    elif timeFilter == "week":
        d = str(datetime.utcnow() - timedelta(hours=168))
    elif timeFilter == "month":
        d = str(datetime.utcnow() - timedelta(hours=730))
    else:
        raise Exception("Wrong time filter!")

    timeAgo = d[:10] + "T" + d[11:19]
    timeAgo = datetime.strptime(timeAgo, "%Y-%m-%dT%H:%M:%S")

    previewCounter = 0
    posts = []
    print("search: ", search_ids)
    for ids in search_ids:
        for i in range(5):
            try:
                p = graph.get_object(
                    ids + "?fields=feed{permalink_url,attachments,message,created_time,comments{comments,message,created_time,from,attachment}}",
                    page=True, retry=5)
                print("facebook pages: ", ids)
                if "feed" in p:
                    for post in p["feed"]["data"]:
                        temp = post["created_time"][:-5]
                        postTime = datetime.strptime(temp, "%Y-%m-%dT%H:%M:%S")
                        if postTime > timeAgo:
                            if "comments" in post:
                                post["comments"] = post["comments"]["data"]
                                for index in range(len(post["comments"])):
                                    post["comments"][index]["indent_number"] = 0
                                    post["comments"][index]["comment_text"] = post["comments"][index].pop("message")
                                    post["comments"][index]["comment_author"] = post["comments"][index]["from"]["name"]
                                    post["comments"][index].pop("from")
                                for comment in post["comments"]:
                                    if "comments" in comment:
                                        comment["comments"] = comment["comments"]["data"]
                                        for subComment in comment["comments"]:
                                            subComment["indent_number"] = 1
                                            subComment["comment_text"] = subComment.pop("message")
                                            subComment["comment_author"] = subComment["from"]["name"]
                                            subComment.pop("from")
                                for index in range(len(post["comments"])):
                                    if "comments" in post["comments"][index]:
                                        post["comments"][index + 1:index + 1] = post["comments"][index]["comments"]
                                        post["comments"][index].pop("comments")
                                post["numberOfComments"] = len(post["comments"])
                            else:
                                post["numberOfComments"] = 0
                            if "message" in post:
                                post["post_text"] = post.pop("message")
                            post["url"] = ""
                            post["source"] = "facebook"
                            post["title"] = ""
                            posts.append(post)
                            previewCounter += 1
                            if isPreview and (previewCounter == 5):
                                break
                        else:
                            break

                break
            except:
                print(ids, "tried again")
        if isPreview and (previewCounter == 5):
            break

    # Sorting all comments with comment numbers, because I will use them in web page in this order
    # posts = sorted(posts, key=lambda k: k["numberOfComments"], reverse=True)
    docs = []
    for submission in posts:
        if not submission["numberOfComments"]:
            continue
        comments = []
        for comment in submission["comments"]:
            comment["relative_indent"] = 0
            comment["created_time"] = comment["created_time"][:10] + " " + comment["created_time"][11:18]
            comments.append(comment)

        submission['created_time'] = datetime.strptime(submission['created_time'][:10], '%Y-%m-%d').strftime('%Y-%m-%d')

        temp = {"title": submission["title"], "source": submission["source"], "comments": comments,
                "url": submission["url"], "numberOfComments": submission["numberOfComments"],
                'subreddit': 'writtenWithHand', 'created_time': submission['created_time']}
        if "post_text" in submission:
            temp["post_text"] = submission["post_text"]
        else:
            temp["post_text"] = ""
        docs.append(temp)
    prev = 0
    for values in docs:
        for current in values["comments"]:
            current["relative_indent"] = current["indent_number"] - prev
            prev = current["indent_number"]

    return docs


def getComments(submission):
    commentStack, comList = [], []
    submission.comments.replace_more(limit=0)
    temp = reversed(submission.comments)
    for x in temp:
        commentStack.append([x, 0, "true", "true"])
    while commentStack:
        comment = commentStack.pop()
        if comment[0].replies:
            temp = reversed(comment[0].replies)
            for x in temp:
                commentStack.append([x, comment[1] + 1, "true", "false"])
            comment[2] = "false"
        s = {
            'submission_id': comment[0]._submission.id,
            'comment_id': comment[0].id,
            'user': comment[0].author.name,
            'timestamp_ms': int(comment[0].created)
        }
        comList.append(s)
    return comList


def mineRedditConversation(subreddits, isPreview, timeFilter='day'):
    keys = Connection.Instance().redditFacebookDB['tokens'].find_one()["reddit"]
    reddit = praw.Reddit(client_id=keys["client_id"],
                         client_secret=keys["client_secret"],
                         user_agent=keys["user_agent"],
                         api_type=keys["api_type"])
    previewCounter = 0
    posts = []
    for subreddit in subreddits:
        s = reddit.subreddit(subreddit)
        print("subreddit: ", subreddit)
        try:
            for submission in s.top(time_filter=timeFilter, limit=None):
                try:
                    print("submission: ", submission)
                    if (re.search(r"^https://www.reddit.com", submission.url) or re.search(r"^https://i.redd.it",
                                                                                           submission.url)):
                        commentStack, comList = [], []
                        submission.comments.replace_more(limit=0)
                        if submission.comments:
                            temp = reversed(submission.comments)
                            for x in temp:
                                commentStack.append([x, 0, "true", "true"])
                            while commentStack:
                                comment = commentStack.pop()
                                if comment[0].replies:
                                    temp = reversed(comment[0].replies)
                                    for x in temp:
                                        commentStack.append([x, comment[1] + 1, "true", "false"])
                                    comment[2] = "false"
                                comList.append(comment)
                        cList = []
                        for c in comList:
                            temp = {"parent": c[0].parent_id[3:], "comment_text": c[0].body,
                                    "created_time": c[0].created,
                                    "comment_id": c[0].id, "indent_number": c[1], "is_leaf": c[2], "is_root": c[3]}
                            if c[0].author:
                                temp["comment_author"] = c[0].author.name
                            else:
                                temp["comment_author"] = "[deleted]"
                            cList.append(temp)

                        posts.append({
                            "source": "reddit",
                            "created_time": submission.created,
                            "title": submission.title,
                            "post_text": submission.selftext,
                            "comments": cList,
                            "url": submission.url,
                            "numberOfComments": len(cList),
                            "subreddit": subreddit
                        })
                        if len(cList) != 0:
                            previewCounter += 1
                        if isPreview and (previewCounter == 5):
                            break

                except:
                    print("one submission passed")
                    pass
        except:
            pass

        if isPreview and (previewCounter == 5):
            break

    docs = []
    for submission in posts:
        if not submission["numberOfComments"]:
            continue
        comments = []
        for comment in submission["comments"]:
            comment["relative_indent"] = 0
            comment["created_time"] = datetime.fromtimestamp(int(comment["created_time"])).strftime("%Y-%m-%d %H:%M:%S")
            comments.append(comment)

        submission['created_time'] = datetime.fromtimestamp(submission['created_time']).strftime('%Y-%m-%d')
        temp = {"title": submission["title"], "source": submission["source"], "comments": comments,
                "url": submission["url"], "numberOfComments": submission["numberOfComments"],
                'subreddit': submission['subreddit'], 'created_time': submission['created_time']}
        if "post_text" in submission:
            temp["post_text"] = submission["post_text"]
        else:
            temp["post_text"] = ""
        docs.append(temp)
    prev = 0
    for values in docs:
        for current in values["comments"]:
            current["relative_indent"] = current["indent_number"] - prev
            prev = current["indent_number"]

    return docs


def sourceSelection(topicList):
    my_token = Connection.Instance().redditFacebookDB['tokens'].find_one()["facebook"]["token"]
    graph = facebook.GraphAPI(access_token=my_token, version="2.7")

    allSearches = []
    for topic in topicList:
        events = []
        s = graph.get_object('search?q=' + topic + '&type=event&limit=100')
        while True:
            try:
                for search in s['data']:
                    events.append({'event_id': search['id'], 'event_name': search['name']})
                s = requests.get(s['paging']['next']).json()
            except:
                break
        allSearches.append({
            'events': events
        })
    return allSearches


def mineEvents(search_id_list, isPreview):
    my_token = Connection.Instance().redditFacebookDB['tokens'].find_one()["facebook"]["token"]
    graph = facebook.GraphAPI(access_token=my_token, version="2.7")
    t = []
    c = 0
    for ids in search_id_list:
        c += 1
        print(ids)

        event = graph.get_object(
            ids + '?fields=attending_count,updated_time,cover,end_time,id,interested_count,name,place,start_time',
            page=True, retry=5)
        if 'end_time' in event:
            event['end_time'] = time.mktime(datetime.strptime(event['end_time'][:10], "%Y-%m-%d").timetuple())
        else:
            event['end_time'] = time.mktime(datetime.strptime(event['start_time'][:10], "%Y-%m-%d").timetuple())
        try:
            if 'location' in event['place']:
                event['place'] = event['place']['location']['city'] + ", " + event['place']['location']['country']
            else:
                event['place'] = event['place']['name']
        except:
            event['place'] = ''
        event['link'] = 'https://www.facebook.com/events/' + event['id']
        event['start_time'] = event['start_time'][:10]
        event['interested'] = event.pop('interested_count')
        event['coming'] = event.pop('attending_count')
        if 'cover' in event:
            event['cover'] = event['cover']['source']

        t.append((event, ids))
        if c == 5:
            break

    return t


def insertEventsIntoDataBase(eventsWithIds, topic_id):
    for event, ids in eventsWithIds:
        ret = Connection.Instance().events[str(topic_id)].aggregate([
            {'$match': {'id': ids}},
            {'$limit': 1}
        ])

        if ret.alive:
            for elem in ret:
                newEventUpdateTime = datetime.strptime(event['updated_time'][:-5], "%Y-%m-%dT%H:%M:%S")
                oldEventUpdateTime = datetime.strptime(elem['updated_time'][:-5], "%Y-%m-%dT%H:%M:%S")
                if newEventUpdateTime != oldEventUpdateTime:
                    print(newEventUpdateTime)
                    print(oldEventUpdateTime)
                if newEventUpdateTime > oldEventUpdateTime:
                    Connection.Instance().events[str(topic_id)].remove({'id': ids})
                    Connection.Instance().events[str(topic_id)].insert_one(event)
                    print('updated')
                else:
                    print('existing')
        else:
            Connection.Instance().events[str(topic_id)].insert_one(event)
            print('added new')


def startEvent(topic_id, topicList):
    sources = sourceSelection(topicList)
    for source in sources:
        ids = []
        for event in source['events']:
            ids.append(event['event_id'])
        eventsWithIds = mineEvents(ids, False)
        insertEventsIntoDataBase(eventsWithIds, topic_id)


def getCommentsOfSubmission(submission):
    commentStack, comList = [], []
    submission.comments.replace_more(limit=0)
    temp = reversed(submission.comments)
    dayAgo = int(round(time.time())) - 86400000
    for x in temp:
        commentStack.append(x)
    while commentStack:
        comment = commentStack.pop()
        if int(comment.created) >= dayAgo:
            try:
                if comment.replies:
                    temp = reversed(comment.replies)
                    for x in temp:
                        commentStack.append(x)
                s = {
                    'submission_id': comment._submission.id,
                    'comment_id': comment.id,
                    'user': comment.author.name,
                    'timestamp_ms': int(comment.created) * 1000
                }
                comList.append(s)
            except:
                pass
    return comList


def searchSubredditNews(topic_id, subredditNames):
    try:
        keys = Connection.Instance().redditFacebookDB['tokens'].find_one()["reddit"]
        reddit = praw.Reddit(client_id=keys["client_id"],
                             client_secret=keys["client_secret"],
                             user_agent=keys["user_agent"],
                             api_type=keys["api_type"])

        submissions = []
        for subredditName in subredditNames:
            for submission in reddit.subreddit(subredditName).top(time_filter='month'):
                if not (re.search(r"^https://www.reddit.com", submission.url) or
                            re.search(r"^https://i.redd.it", submission.url) or
                            re.search(r"imgur.com", submission.url) or
                            re.search(r".mp4$", submission.url)):
                    submissions.append(submission)

        for submission in submissions:
            mentions = getCommentsOfSubmission(submission)
            s = {
                'channel': 'reddit',
                'url': submission.url,
                'topic_id': topic_id,
                'mentions': mentions
            }

            if len(mentions) != 0:
                link_parser.calculateLinks(s)
    except:
        print(subredditName)
        pass


# day filter can be 'day', 'week', 'month'; default is 'day'
def searchFacebookNews(topic_id, search_ids):
    my_token = Connection.Instance().redditFacebookDB['tokens'].find_one()["facebook"]["token"]
    graph = facebook.GraphAPI(access_token=my_token, version="2.7")

    dayAgo = (int(round(time.time())) - 86400000) * 1000

    for id in search_ids:
        p = graph.get_object(str(
            id) + '?fields=feed{link,created_time,id,comments{from,id,created_time,comments{from,id,created_time}}}',
                             page=True, retry=5)
        if 'feed' in p:
            for post in p['feed']['data']:
                d = post['created_time']
                created_time = d[:10] + "T" + d[11:19]
                created_time = datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S").timestamp() * 1000
                if dayAgo < created_time:
                    if ('link' in post) and not (re.search('facebook', post['link'])):
                        listOfMention = []
                        if 'comments' in post:
                            for comment in post['comments']['data']:
                                if 'comments' in comment:
                                    for subComment in comment['comments']['data']:
                                        d = subComment['created_time']
                                        created_comment_time = d[:10] + "T" + d[11:19]
                                        created_comment_time = datetime.strptime(created_comment_time,
                                                                                 "%Y-%m-%dT%H:%M:%S").timestamp() * 1000
                                        listOfMention.append({
                                            'submission_id': post['id'],
                                            'comment_id': subComment['id'],
                                            'user': subComment['from']['id'],
                                            'timestamp_ms': int(created_comment_time)
                                        })
                                d = comment['created_time']
                                created_comment_time = d[:10] + "T" + d[11:19]
                                created_comment_time = datetime.strptime(created_comment_time,
                                                                         "%Y-%m-%dT%H:%M:%S").timestamp() * 1000
                                listOfMention.append({
                                    'submission_id': post['id'],
                                    'comment_id': comment['id'],
                                    'user': comment['from']['id'],
                                    'timestamp_ms': int(created_comment_time)
                                })
                        if len(listOfMention) != 0:
                            link_parser.calculateLinks({
                                'channel': 'facebook',
                                'url': post['link'],
                                'topic_id': topic_id,
                                'mentions': listOfMention
                            })
                else:
                    break


'''
def mineEvents(topicList):
    client = MongoClient('localhost', 27017)
    db = client['tes']
    my_token = db.tokens.find_one()['eventbrite']['token']
    collection = db.eventbrite_events
    for topic in topicList:
        response = requests.get(
            "https://www.eventbriteapi.com/v3/events/search/",
            headers = {
                "Authorization": "Bearer " + my_token,
            },
            params = {
                'q' : topic
            },
            verify = True,  # Verify SSL certificate
        )
        response = response.json()
        for event in response['events']:
            ret = db.eventbrite_events.aggregate([
                {'$match': { 'event.id': event['id']}},
                {'$limit': 1}
            ])

            if ret.alive:
                print("alive")
                for elem in ret:
                    collection.delete_one({'event.id' : event['id']})

            collection.insert_one({'topic':topic, 'event':event})
'''

if __name__ == '__main__':

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id, keywords "
            "FROM topics"
        )
        cur.execute(sql)
        var = cur.fetchall()

        dates = ["day", "week", "month"]
        for v in var:
            startEvent(v[0], v[1].split(","))
            with Connection.Instance().get_cursor() as cur:
                sql = (
                    "SELECT ARRAY_agg(facebook_page_id) as pages "
                    "FROM topic_facebook_page "
                    "WHERE topic_id = %s "
                    "GROUP BY topic_id"
                )
                cur.execute(sql, [v[0]])
                pages = cur.fetchone()

                sql = (
                    "SELECT ARRAY_agg(subreddit) as subreddits "
                    "FROM topic_subreddit "
                    "WHERE topic_id = %s "
                    "GROUP BY topic_id"
                )
                cur.execute(sql, [v[0]])
                subreddits = cur.fetchone()

                if subreddits is not None and len(subreddits):
                    searchSubredditNews(v[0], subreddits[0])
                if pages is not None and len(subreddits):
                    searchFacebookNews(v[0], pages[0])

                for date in dates:
                    posts = []
                    if subreddits is not None and len(subreddits):
                        posts.extend(mineRedditConversation(subreddits[0], False, date))
                    if pages is not None and len(pages):
                        posts.extend(mineFacebookConversations(pages[0], False, date))
                    if len(posts) != 0:
                        posts = sorted(posts, key=lambda k: k["numberOfComments"], reverse=True)
                        Connection.Instance().conversations[str(v[0])].remove({"time_filter": date})
                        Connection.Instance().conversations[str(v[0])].insert_one({'time_filter': date, 'posts': posts})
