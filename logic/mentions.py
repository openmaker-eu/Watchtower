__author__ = ['Enis Simsar']

from application.Connections import Connection
from datetime import datetime, timedelta


def get_mention_aggregations(topic_id):
    aggregated_mentions = {}
    length_mentions = {}
    table_data = {}
    days = Connection.Instance().daily_mentions[str(topic_id)].find()
    today = datetime.today().date()
    last_week = (datetime.today() - timedelta(days=7)).date()
    last_month = (datetime.today() - timedelta(days=30)).date()
    for day in days:
        mentions = day['mention']
        date = day['modified_date'].strftime("%d-%m-%Y")
        for mention_tuple in mentions:
            mention = mention_tuple['mention_username']
            count = mention_tuple['count']

            if mention not in table_data:
                table_data[mention] = {
                    'today': [],
                    'week': [],
                    'month': []
                }
                if day['modified_date'].date() == today:
                    table_data[mention]['today'] = [count]
                    table_data[mention]['week'] = [count]
                    table_data[mention]['month'] = [count]
                elif day['modified_date'].date() > last_week:
                    table_data[mention]['today'] = []
                    table_data[mention]['week'] = [count]
                    table_data[mention]['month'] = [count]
                elif day['modified_date'].date() > last_month:
                    table_data[mention]['today'] = []
                    table_data[mention]['week'] = []
                    table_data[mention]['month'] = [count]
            else:
                if day['modified_date'].date() == today:
                    counts = table_data[mention]['today']
                    counts.append(count)
                    table_data[mention]['today'] = counts

                    counts = table_data[mention]['week']
                    counts.append(count)
                    table_data[mention]['week'] = counts

                    counts = table_data[mention]['month']
                    counts.append(count)
                    table_data[mention]['month'] = counts

                elif day['modified_date'].date() > last_week:
                    counts = table_data[mention]['week']
                    counts.append(count)
                    table_data[mention]['week'] = counts

                    counts = table_data[mention]['month']
                    counts.append(count)
                    table_data[mention]['month'] = counts
                elif day['modified_date'].date() > last_month:
                    counts = table_data[mention]['month']
                    counts.append(count)
                    table_data[mention]['month'] = counts

            if mention not in length_mentions:
                length_mentions[mention] = count
            else:
                length_mentions[mention] = length_mentions[mention] + count
            if mention not in aggregated_mentions:
                aggregated_mentions[mention] = {}
                aggregated_mentions[mention]['labels'] = [date]
                aggregated_mentions[mention]['data'] = [count]
            else:
                labels = aggregated_mentions[mention]['labels']
                labels.append(date)
                aggregated_mentions[mention]['labels'] = labels

                data = aggregated_mentions[mention]['data']
                data.append(count)
                aggregated_mentions[mention]['data'] = data
    sorted_length = sorted(length_mentions, key=lambda k: length_mentions[k], reverse=True)[:50]
    return {
        'sorted': sorted_length,
        'data': aggregated_mentions,
        'table_data': table_data
    }
