__author__ = ['Enis Simsar']

from application.Connections import Connection
from datetime import datetime, timedelta


def topic_hashtag(topic_id, hashtag, save_type):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM topic_hashtag where topic_id = %s AND hashtag = %s)"
        )
        cur.execute(sql, [int(topic_id), hashtag])
        fetched = cur.fetchone()

        if fetched[0]:
            if not save_type:
                return
            else:
                sql = (
                    "DELETE FROM topic_hashtag "
                    "WHERE topic_id = %s AND hashtag = %s;"
                )
                cur.execute(sql, [int(topic_id), hashtag])
        else:
            if not save_type:
                sql = (
                    "INSERT INTO topic_hashtag "
                    "(topic_id, hashtag) "
                    "VALUES (%s, %s);"
                )
                cur.execute(sql, [int(topic_id), hashtag])
            else:
                return


def get_hashtag_aggregations(topic_id):
    aggregated_hashtags = {}
    length_hashtags = {}
    table_data = {}
    days = Connection.Instance().daily_hastags[str(topic_id)].find()
    today = datetime.today().date()
    last_week = (datetime.today() - timedelta(days=7)).date()
    last_month = (datetime.today() - timedelta(days=30)).date()
    for day in days:
        hashtags = day['hashtag']
        date = day['modified_date'].strftime("%d-%m-%Y")
        for hashtag_tuple in hashtags:
            hashtag = hashtag_tuple['hashtag']
            count = hashtag_tuple['count']
            if hashtag not in table_data:
                table_data[hashtag] = {
                    'today': [],
                    'week': [],
                    'month': []
                }
                if day['modified_date'].date() == today:
                    table_data[hashtag]['today'] = [count]
                    table_data[hashtag]['week'] = [count]
                    table_data[hashtag]['month'] = [count]
                elif day['modified_date'].date() > last_week:
                    table_data[hashtag]['today'] = []
                    table_data[hashtag]['week'] = [count]
                    table_data[hashtag]['month'] = [count]
                elif day['modified_date'].date() > last_month:
                    table_data[hashtag]['today'] = []
                    table_data[hashtag]['week'] = []
                    table_data[hashtag]['month'] = [count]
            else:
                if day['modified_date'].date() == today:
                    counts = table_data[hashtag]['today']
                    counts.append(count)
                    table_data[hashtag]['today'] = counts

                    counts = table_data[hashtag]['week']
                    counts.append(count)
                    table_data[hashtag]['week'] = counts

                    counts = table_data[hashtag]['month']
                    counts.append(count)
                    table_data[hashtag]['month'] = counts

                elif day['modified_date'].date() > last_week:
                    counts = table_data[hashtag]['week']
                    counts.append(count)
                    table_data[hashtag]['week'] = counts

                    counts = table_data[hashtag]['month']
                    counts.append(count)
                    table_data[hashtag]['month'] = counts
                elif day['modified_date'].date() > last_month:
                    counts = table_data[hashtag]['month']
                    counts.append(count)
                    table_data[hashtag]['month'] = counts

            if hashtag not in length_hashtags:
                length_hashtags[hashtag] = count
            else:
                length_hashtags[hashtag] = length_hashtags[hashtag] + count

            if hashtag not in aggregated_hashtags:
                aggregated_hashtags[hashtag] = {
                    'all': {},
                    'week': {},
                    'month': {}
                }
                aggregated_hashtags[hashtag]['all']['labels'] = [date]
                aggregated_hashtags[hashtag]['all']['data'] = [count]

                if day['modified_date'].date() > last_week:
                    aggregated_hashtags[hashtag]['week']['labels'] = [date]
                    aggregated_hashtags[hashtag]['week']['data'] = [count]

                    aggregated_hashtags[hashtag]['month']['labels'] = [date]
                    aggregated_hashtags[hashtag]['month']['data'] = [count]
                elif day['modified_date'].date() > last_month:
                    aggregated_hashtags[hashtag]['week']['labels'] = []
                    aggregated_hashtags[hashtag]['week']['data'] = []

                    aggregated_hashtags[hashtag]['month']['labels'] = [date]
                    aggregated_hashtags[hashtag]['month']['data'] = [count]
                else:
                    aggregated_hashtags[hashtag]['week']['labels'] = []
                    aggregated_hashtags[hashtag]['week']['data'] = []

                    aggregated_hashtags[hashtag]['month']['labels'] = []
                    aggregated_hashtags[hashtag]['month']['data'] = []

            else:
                labels = aggregated_hashtags[hashtag]['all']['labels']
                labels.append(date)
                aggregated_hashtags[hashtag]['all']['labels'] = labels

                data = aggregated_hashtags[hashtag]['all']['data']
                data.append(count)
                aggregated_hashtags[hashtag]['all']['data'] = data

                if day['modified_date'].date() > last_week:
                    labels = aggregated_hashtags[hashtag]['week']['labels']
                    labels.append(date)
                    aggregated_hashtags[hashtag]['week']['labels'] = labels

                    data = aggregated_hashtags[hashtag]['week']['data']
                    data.append(count)
                    aggregated_hashtags[hashtag]['week']['data'] = data

                    labels = aggregated_hashtags[hashtag]['month']['labels']
                    labels.append(date)
                    aggregated_hashtags[hashtag]['month']['labels'] = labels

                    data = aggregated_hashtags[hashtag]['month']['data']
                    data.append(count)
                    aggregated_hashtags[hashtag]['month']['data'] = data
                elif day['modified_date'].date() > last_month:
                    labels = aggregated_hashtags[hashtag]['month']['labels']
                    labels.append(date)
                    aggregated_hashtags[hashtag]['month']['labels'] = labels

                    data = aggregated_hashtags[hashtag]['month']['data']
                    data.append(count)
                    aggregated_hashtags[hashtag]['month']['data'] = data

    sorted_length = sorted(length_hashtags, key=lambda k: length_hashtags[k], reverse=True)[:50]
    return {
        'sorted': sorted_length,
        'data': aggregated_hashtags,
        'table_data': table_data
    }
