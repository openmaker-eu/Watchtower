from crontab import CronTab
from os.path import dirname, abspath
from decouple import config

cron_directory = dirname(dirname(abspath(__file__))) + "/crontab_module/crons/"

my_cron = CronTab(user="root")

my_cron.remove_all()
my_cron.write()


cmd_1 = "python3 " + cron_directory + "date_filter.py >> /tmp/date_filter.txt"
job_1  = my_cron.new(command=cmd_1)
job_1.setall("0 */1 * * *")

cmd_2 = "python3 " + cron_directory + "facebook_reddit_crontab.py >> /tmp/facebook_reddit_crontab.txt"
job_2  = my_cron.new(command=cmd_2)
job_2.setall("0 3 * * *")

cmd_3 = "python3 " + cron_directory + "hashtagcrontab.py >> /tmp/hashtagcrontab.txt"
job_3  = my_cron.new(command=cmd_3)
job_3.setall("0 1 * * *")

cmd_4 = "python3 " + cron_directory + "get_influencers.py >> /tmp/get_influencers.txt"
job_4  = my_cron.new(command=cmd_4)
job_4.setall("0 0 * * 1")

cmd_5 = "python3 " + cron_directory + "clear_db_one_month.py >> /tmp/clear_db_one_month.txt"
job_5  = my_cron.new(command=cmd_5)
job_5.setall("0 1 * * 1")

cmd_6 = "python3 " + cron_directory + "get_audience_sample.py " + config("LOCATION") + " " + config("GETFORALLLOCATIONS") + " >> /tmp/get_audience_sample.txt"
job_6  = my_cron.new(command=cmd_6)
job_6.setall("0 */3 * * *")

"""
cmd_7 = "python3 " + cron_directory + "get_follower_ids.py  " + config("FOLLOWERS_LIMIT") + " >> /tmp/get_follower_ids.txt"
job_7  = my_cron.new(command=cmd_7)
job_7.setall("0 0 */2 * *")

cmd_8 = "python3 " + cron_directory + "get_local_influencers.py >> /tmp/get_local_influencers.txt"
job_8  = my_cron.new(command=cmd_8)
job_8.setall("0 */3 * * *")
"""

cmd_9 = "python3 " + cron_directory + "get_events.py >> /tmp/get_events.txt"
job_9  = my_cron.new(command=cmd_9)
job_9.setall("0 3 * * *")

my_cron.write()
