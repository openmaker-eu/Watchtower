__author__ = ['Enis Simsar']

from application.Connections import Connection

def get_crons_log():
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT cron_name, started_at, ended_at, status, frequency "
            "FROM crons_log "
            "WHERE id IN ("
            "SELECT MAX(id) "
            "FROM crons_log "
            "GROUP BY cron_name"
            ") ORDER BY cron_name;"
        )
        cur.execute(sql, [])
        fetched = cur.fetchall()

        if fetched:
            def get_duration(x, y):
                if y is None: return "-"
                diff = y - x
                days, seconds = diff.days, diff.seconds
                hours = days * 24 + seconds // 3600
                minutes = (seconds % 3600) // 60
                seconds = seconds % 60

                if hours == 0 and minutes == 0:
                    return "{0} seconds".format(seconds)
                elif hours == 0:
                    return "{0} min, {1} seconds".format(minutes, seconds)

                return "{0} h, {1} min, {2} sec.".format(hours, minutes, seconds)

            return [{'cron_name': cron[0], 'started_at': cron[1], 'ended_at': cron[2], 'status': cron[3],
                     'duration': get_duration(cron[1], cron[2]), 'frequency': cron[4]} for cron in fetched]

        return []