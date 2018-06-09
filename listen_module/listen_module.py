from time import sleep
import sys
from decouple import config

sys.path.insert(0, config('ROOT_DIR'))

from application.Connections import Connection
from .twitter_stream_thread import StreamCreator
from models.Topic import Topic


class TwitterListen:
    def __init__(self):
        self.topic_dic = {}
        self.thread = None

    def setup(self, topic_list):
        if len(topic_list) != 0:
            for topic in topic_list:
                if str(topic['topic_id']) not in self.topic_dic:
                    self.topic_dic[str(topic['topic_id'])] = topic
            self.thread = StreamCreator(self.topic_dic)
            self.thread.start()

    def restart(self, topic_list):
        self.topic_dic = {}
        if self.thread is not None:
            self.kill()
        if len(topic_list) != 0:
            for alert in topic_list:
                if str(alert['topic_id']) not in self.topic_dic:
                    self.topic_dic[str(alert['topic_id'])] = alert
            self.thread = StreamCreator(self.topic_dic)
            self.thread.start()

    def kill(self):
        self.thread.terminate()
        del self.thread
        self.thread = None


def main():
    running_topic_list = Topic.find_all([('is_running', True)])
    twitter_module = TwitterListen()
    twitter_module.setup(running_topic_list)
    try:
        last_sequence_id = str(Connection.Instance().db["counters"].find_one({'_id': "tweetDBId"})['seq'])
    except:
        last_sequence_id = 0
        pass

    count = 0
    while True:
        print("Loop is continuing. count = {0}".format(count))
        count += 1
        sleep(300)
        new_running_topic_list = Topic.find_all([('is_running', True)])
        if new_running_topic_list != running_topic_list:
            running_topic_list = new_running_topic_list
            print("Restarting Twitter Module!")
            twitter_module.restart(new_running_topic_list)
        if count%6 == 0:
            new_last_sequence_id = str(Connection.Instance().db["counters"].find_one({'_id': "tweetDBId"})['seq'])
            print("last_id = {0}, new_last_id = {1}".format(last_sequence_id, new_last_sequence_id))
            if last_sequence_id == new_last_sequence_id:
                running_topic_list = new_running_topic_list
                print("Unexpectedly Stopped Module, Restarting...")
                twitter_module.restart(new_running_topic_list)
            last_sequence_id = new_last_sequence_id


if __name__ == "__main__":
    main()
