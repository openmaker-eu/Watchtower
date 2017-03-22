from addAlert import AddAlert
from app import webserverInit
from logic import getAllAlertList, setupServer

mainT = AddAlert()
mainT.setup(getAllAlertList())
setupServer()
webserverInit(mainT)
