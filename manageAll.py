from addTrack import AddTrack
from app import webserverInit
from logic import getAllAlertList, setupServer

mainT = AddTrack()
mainT.setup(getAllAlertList())
setupServer()
webserverInit(mainT)
