from addAlert import AddAlert
from app import webserverInit
from logic import getAllRunningAlertList

mainT = AddAlert()
#mainT.setup(getAllRunningAlertList())
webserverInit(mainT)
