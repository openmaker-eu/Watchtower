from addTrack import AddTrack
from app import webserverInit
from logic import getAlertList
import sys
reload(sys)
sys.setdefaultencoding('utf8')

mainT = AddTrack()
mainT.setup(getAlertList())
webserverInit(mainT)
