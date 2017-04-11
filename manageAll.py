from addAlert import AddAlert
from app import webserverInit
from logic import getAllRunningAlertList
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

mainT = AddAlert()
#mainT.setup(getAllRunningAlertList())
webserverInit(mainT)
