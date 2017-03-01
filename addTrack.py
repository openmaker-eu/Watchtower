from track import StreamCreator
import sys
reload(sys)
sys.setdefaultencoding('utf8')

class AddTrack():
    def __init__(self):
        self.threadDic = {}

    def setup(self,alertList):
        for alert in alertList :
            if str(alert['alertid']) not in self.threadDic:
                self.threadDic[str(alert['alertid'])] = StreamCreator(alert)
                self.threadDic[str(alert['alertid'])].start()

    def killAllThreads(self):
        for alert in self.threadDic:
            self.threadDic[alert].terminate()

    def getThreadDic(self):
        return self.threadDic

    def setThreadDic(self, newDic):
        self.threadDic = newDic

    def addThread(self, alert):
        self.threadDic[str(alert['alertid'])] = StreamCreator(alert)
        self.threadDic[str(alert['alertid'])].start()

    def killThread(self, alert):
        self.threadDic[str(alert['alertid'])].terminate()
        del self.threadDic[str(alert['alertid'])] #sonradan ekledik

    def __getitem__(self):
        return (self.threadDic)
