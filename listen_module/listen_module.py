import sys
from datetime import datetime
from time import sleep

sys.path.append('./')

from application.Connections import Connection
from logic import get_all_running_topics_list
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
    running_topic_list = get_all_running_topics_list()
    twitter_module = TwitterListen()
    twitter_module.setup(running_topic_list)
    current_hour = datetime.now().hour
    last_sequence_id = str(Connection.Instance().db["counters"].find_one({'_id': "tweetDBId"})['seq'])

    count = 0
    while True:
        print("Loop is continuing. count = {0}".format(count))
        count += 1
        sleep(300)
        new_running_topic_list = get_all_running_topics_list()
        if new_running_topic_list != running_topic_list:
            running_topic_list = new_running_topic_list
            print("Restarting Twitter Module!")
            twitter_module.restart(new_running_topic_list)
        if count%6 == 0:
            new_last_sequence_id = str(Connection.Instance().db["counters"].find_one({'_id': "tweetDBId"})['seq'])
            print("last_id = {0}, new_last_id = {1}".format(last_sequence_id, new_last_sequence_id))
            if last_sequence_id == new_last_sequence_id:
                last_sequence_id = new_last_sequence_id
                running_topic_list = new_running_topic_list
                print("Unexpectedly Stopped Module, Restarting...")
                twitter_module.restart(new_running_topic_list)


if __name__ == "__main__":
    main()
