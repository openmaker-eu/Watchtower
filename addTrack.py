from track import StreamCreator

class AddTrack():
    def __init__(self):
        self.threadDic = {}

    def setup(self,alertList):
        for alert in alertList :
            if alert['id'] not in self.threadDic:
                self.threadDic[alert['id']] = StreamCreator(alert)
                self.threadDic[alert['id']].start()

    def killAllThreads(self):
        for alert in self.threadDic:
            self.threadDic[alert].terminate()

    def getThreadDic():
        return self.threadDic

    def setThreadDic(newDic):
        self.threadDic = newDic

    def addThread(self, alert):
        self.threadDic[alert['id']] = StreamCreator(alert)
        self.threadDic[alert['id']].start()

    def killThread(self, alert):
        self.threadDic[alert['id']].terminate()

    def __getitem__(self):
        return (self.threadDic)
