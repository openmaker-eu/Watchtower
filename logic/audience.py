__author__ = ['Kemal Berk Kocabagli', 'Enis Simsar']

from application.Connections import Connection


def get_recommended_audience(topic_id, location, filter_type, user_id, cursor):
    result = {}
    if filter_type == "rated":
        # fetch rated audience
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT audience_id "
                "FROM user_audience_rating "
                "WHERE user_id = %s and topic_id = %s ;"
            )
            cur.execute(sql, [int(user_id), int(topic_id)])
            rated_audience = cur.fetchall()
            rated_audience = [aud_member[0] for aud_member in rated_audience]
            audience = Connection.Instance().audienceDB['all_audience'].find({'id': {'$in': rated_audience}})

    elif filter_type == "recommended":
        # fetch recommended audience
        audience = Connection.Instance().audience_samples_DB[str(location) + '_' + str(topic_id)].find({})

    else:
        print("Please provide a valid filter. \"rated\" or \"recommended\"")
        return
    audience = list(audience)[cursor:cursor + 21]

    audience_ids = []
    if len(audience) != 0:
        audience_ids = [aud_member['id'] for aud_member in audience]

    if len(audience_ids) == 0:
        audience_ids = [-1]

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT audience_id, rating "
            "FROM user_audience_rating "
            "WHERE user_id = %s and topic_id = %s and audience_id IN %s"
        )
        cur.execute(sql, [int(user_id), int(topic_id), tuple(audience_ids)])
        rating_list = cur.fetchall()
        ratings = {str(rating[0]): rating[1] for rating in rating_list}

    for aud_member in audience:
        aud_member['rate'] = 0
        try:
            aud_member['rate'] = ratings[str(aud_member['id'])]
        except KeyError:
            pass

    cursor = int(cursor) + 21
    if cursor >= 500 or len(audience) == 0:
        cursor = 0
    result['next_cursor'] = cursor
    result['cursor_length'] = 500
    result['audience'] = audience
    return result


def rate_audience(topic_id, user_id, audience_id, rating):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS "
            "(SELECT 1 FROM user_audience_rating where user_id = %s and topic_id = %s and audience_id = %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_id), int(audience_id)])
        fetched = cur.fetchone()

        if fetched[0]:
            if float(rating) != 0.0:
                sql = (
                    "UPDATE user_audience_rating "
                    "SET rating = %s "
                    "WHERE user_id = %s and audience_id = %s and topic_id = %s"
                )
                cur.execute(sql, [float(rating), int(user_id), int(audience_id), int(topic_id)])
            else:
                sql = (
                    "DELETE FROM user_audience_rating "
                    "WHERE user_id = %s and audience_id = %s and topic_id = %s"
                )
                cur.execute(sql, [int(user_id), int(audience_id), int(topic_id)])
        else:
            if float(rating) != 0.0:
                sql = (
                    "INSERT INTO user_audience_rating "
                    "(user_id, audience_id, topic_id, rating) "
                    "VALUES (%s, %s, %s, %s)"
                )
                cur.execute(sql, [int(user_id), int(audience_id), int(topic_id), float(rating)])

def get_audience(topic_id, user_id, cursor, location):
    print("In get audience")
    if topic_id is None:
        print("Topic is not defined.")
    print("Topic " + str(topic_id))
    print("Location " + str(location))
    print("Cursor " + str(cursor))
    result = {}
    audiences = list(Connection.Instance().audience_samples_DB[str(location) + "_" + str(topic_id)].find({}))[
                cursor:cursor + 21]
    audience_ids = []
    if len(audiences) != 0:
        audience_ids = [audience['id'] for audience in audiences]

    if len(audience_ids) == 0:
        audience_ids = [-1]

    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT audience_id, rating "
            "FROM user_audience_rating "
            "WHERE user_id = %s and topic_id = %s and audience_id IN %s"
        )
        cur.execute(sql, [int(user_id), int(topic_id), tuple(audience_ids)])
        rating_list = cur.fetchall()
        ratings = {str(rating[0]): rating[1] for rating in rating_list}

    for audience in audiences:
        audience['rate'] = 0
        try:
            audience['rate'] = ratings[str(audience['id'])]
        except KeyError:
            pass

    cursor = int(cursor) + 21
    if cursor >= 500 or len(audiences) == 0:
        cursor = 0
    result['next_cursor'] = cursor
    result['cursor_length'] = 500
    result['audiences'] = audiences
    return result


def get_audience_stats(topic_id, location):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT execution_duration, last_executed, from_predicted_location, from_regex "
            "FROM audience_samples_last_executed "
            "WHERE topic_id = %(topic_id)s and location = %(location)s "
        )

        params = {
            'topic_id': int(topic_id),
            'location': location,
        }

        cur.execute(sql, params)
        audience_stats = {}

        execution_duration, last_executed, from_predicted_location, from_regex = cur.fetchall()[0]

        audience_stats['topic_id'] = int(topic_id)
        audience_stats['location'] = str(location)
        audience_stats['execution_duration'] = round(execution_duration.total_seconds(), 2)
        audience_stats['last_executed'] = last_executed.date()
        audience_stats['from_predicted_location'] = from_predicted_location
        audience_stats['from_regex'] = from_regex

        return audience_stats
