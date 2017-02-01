from addTrack import AddTrack
from app import webserverInit
from logic import getAlertList, setupServer
import sys
reload(sys)
sys.setdefaultencoding('utf8')

mainT = AddTrack()
setupServer()
mainT.setup(getAlertList())
webserverInit(mainT)
