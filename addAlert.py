from track import StreamCreator
import sys
reload(sys)
sys.setdefaultencoding('utf8')

class AddAlert():
    def __init__(self):
        self.alertDic = {}
        self.onlyThread = None

    def setup(self,alertList):
        if len(alertList) != 0:
            for alert in alertList :
                if str(alert['alertid']) not in self.alertDic:
                    self.alertDic[str(alert['alertid'])] = alert
            print self.alertDic
            self.onlyThread = StreamCreator(self.alertDic)
            self.onlyThread.start()

    def addAlert(self, alert):
        self.alertDic[str(alert['alertid'])] = alert
        if self.onlyThread is not None:
            self.killThread()
        self.onlyThread = StreamCreator(self.alertDic)
        self.onlyThread.start()

    def delAlert(self, alert):
        del self.alertDic[str(alert['alertid'])]
        if self.onlyThread is not None:
            self.killThread()
        if len(self.alertDic) != 0:
            self.onlyThread = StreamCreator(self.alertDic)
            self.onlyThread.start()

    def updateAlert(self, alert):
        del self.alertDic[str(alert['alertid'])]
        self.addAlert(alert)

    def killThread(self):
        self.onlyThread.terminate()
        self.onlyThread = None

    def checkThread(self):
        print "thread status: " + str(self.onlyThread.checkAlive())

    def __getitem__(self):
        return (self.threadDic)
