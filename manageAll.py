from addTrack import AddTrack
from app import webserverInit
import sys
reload(sys)
sys.setdefaultencoding('utf8')

mainT = AddTrack()
webserverInit(mainT)
