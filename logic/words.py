__author__ = ['Enis Simsar']

from application.Connections import Connection
from datetime import datetime, timedelta


def get_words_aggregations(topic_id):
    aggregated_words = {}
    length_words = {}
    table_data = {}
    days = Connection.Instance().daily_words[str(topic_id)].find()
    today = datetime.today().date()
    last_week = (datetime.today() - timedelta(days=7)).date()
    last_month = (datetime.today() - timedelta(days=30)).date()
    for day in days:
        words = day['words']
        date = day['modified_date'].strftime("%d-%m-%Y")
        for word_tuple in words:
            word = word_tuple['word']
            count = word_tuple['count']

            if word not in table_data:
                table_data[word] = {
                    'today': [],
                    'week': [],
                    'month': []
                }
                if day['modified_date'].date() == today:
                    table_data[word]['today'] = [count]
                    table_data[word]['week'] = [count]
                    table_data[word]['month'] = [count]
                elif day['modified_date'].date() > last_week:
                    table_data[word]['today'] = []
                    table_data[word]['week'] = [count]
                    table_data[word]['month'] = [count]
                elif day['modified_date'].date() > last_month:
                    table_data[word]['today'] = []
                    table_data[word]['week'] = []
                    table_data[word]['month'] = [count]
            else:
                if day['modified_date'].date() == today:
                    counts = table_data[word]['today']
                    counts.append(count)
                    table_data[word]['today'] = counts

                    counts = table_data[word]['week']
                    counts.append(count)
                    table_data[word]['week'] = counts

                    counts = table_data[word]['month']
                    counts.append(count)
                    table_data[word]['month'] = counts

                elif day['modified_date'].date() > last_week:
                    counts = table_data[word]['week']
                    counts.append(count)
                    table_data[word]['week'] = counts

                    counts = table_data[word]['month']
                    counts.append(count)
                    table_data[word]['month'] = counts
                elif day['modified_date'].date() > last_month:
                    counts = table_data[word]['month']
                    counts.append(count)
                    table_data[word]['month'] = counts

            if word not in length_words:
                length_words[word] = count
            else:
                length_words[word] = length_words[word] + count

            if word not in aggregated_words:
                aggregated_words[word] = {
                    'all': {},
                    'week': {},
                    'month': {}
                }
                aggregated_words[word]['all']['labels'] = [date]
                aggregated_words[word]['all']['data'] = [count]

                if day['modified_date'].date() > last_week:
                    aggregated_words[word]['week']['labels'] = [date]
                    aggregated_words[word]['week']['data'] = [count]

                    aggregated_words[word]['month']['labels'] = [date]
                    aggregated_words[word]['month']['data'] = [count]
                elif day['modified_date'].date() > last_month:
                    aggregated_words[word]['week']['labels'] = []
                    aggregated_words[word]['week']['data'] = []

                    aggregated_words[word]['month']['labels'] = [date]
                    aggregated_words[word]['month']['data'] = [count]
                else:
                    aggregated_words[word]['week']['labels'] = []
                    aggregated_words[word]['week']['data'] = []

                    aggregated_words[word]['month']['labels'] = []
                    aggregated_words[word]['month']['data'] = []

            else:
                labels = aggregated_words[word]['all']['labels']
                labels.append(date)
                aggregated_words[word]['all']['labels'] = labels

                data = aggregated_words[word]['all']['data']
                data.append(count)
                aggregated_words[word]['all']['data'] = data

                if day['modified_date'].date() > last_week:
                    labels = aggregated_words[word]['week']['labels']
                    labels.append(date)
                    aggregated_words[word]['week']['labels'] = labels

                    data = aggregated_words[word]['week']['data']
                    data.append(count)
                    aggregated_words[word]['week']['data'] = data

                    labels = aggregated_words[word]['month']['labels']
                    labels.append(date)
                    aggregated_words[word]['month']['labels'] = labels

                    data = aggregated_words[word]['month']['data']
                    data.append(count)
                    aggregated_words[word]['month']['data'] = data
                elif day['modified_date'].date() > last_month:
                    labels = aggregated_words[word]['month']['labels']
                    labels.append(date)
                    aggregated_words[word]['month']['labels'] = labels

                    data = aggregated_words[word]['month']['data']
                    data.append(count)
                    aggregated_words[word]['month']['data'] = data

    sorted_length = sorted(length_words, key=lambda k: length_words[k], reverse=True)[:50]
    return {
        'sorted': sorted_length,
        'data': aggregated_words,
        'table_data': table_data
    }
