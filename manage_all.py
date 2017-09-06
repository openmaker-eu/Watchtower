from topic_controller import AddAlert
from app import webserverInit
from logic import getAllRunningAlertList

mainT = AddAlert()
mainT.setup(getAllRunningAlertList())
webserverInit(mainT)
