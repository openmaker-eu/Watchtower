import sys
from datetime import datetime
from time import sleep

sys.path.append('./')

from application.Connections import Connection
from logic import getAllRunningAlertList
from twitter_stream_thread import StreamCreator


class TwitterListen():
    def __init__(self):
        self.topic_dic = {}
        self.thread = None

    def setup(self, topic_list):
        if len(topic_list) != 0:
            for alert in topic_list:
                if str(alert['alertid']) not in self.topic_dic:
                    self.topic_dic[str(alert['alertid'])] = alert
            self.thread = StreamCreator(self.topic_dic)
            self.thread.start()

    def restart(self, topic_list):
        self.topic_dic = {}
        if self.thread is not None:
            self.kill()
        if len(topic_list) != 0:
            for alert in topic_list:
                if str(alert['alertid']) not in self.topic_dic:
                    self.topic_dic[str(alert['alertid'])] = alert
            self.thread = StreamCreator(self.topic_dic)
            self.thread.start()

    def kill(self):
        self.thread.terminate()
        del self.thread
        self.thread = None


def main():
    running_topic_list = getAllRunningAlertList()
    twitter_module = TwitterListen()
    twitter_module.setup(running_topic_list)
    current_hour = datetime.now().hour
    last_sequence_id = Connection.Instance().db["counters"].find_one({'_id': "tweetDBId"})['seq']

    while True:
        new_running_topic_list = getAllRunningAlertList()

        if new_running_topic_list != running_topic_list:
            running_topic_list = new_running_topic_list
            print("Restarting Twitter Module!")
            twitter_module.restart(new_running_topic_list)
        if current_hour != datetime.now().hour:
            current_hour = datetime.now().hour
            if last_sequence_id == Connection.Instance().db["counters"].find_one({'_id': "tweetDBId"})['seq']:
                running_topic_list = new_running_topic_list
                print("Unexpectedly Stopped Module, Restarting...")
                twitter_module.restart(new_running_topic_list)

        sleep(450)


if __name__ == "__main__":
    main()