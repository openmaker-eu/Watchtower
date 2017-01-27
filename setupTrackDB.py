import dbM

dbName = 'openMakerdB'
c_connect = dbM.connection_try() #try to connect pymongo
db_listener = dbM.handle_db(c_connect,dbName) #create and handle a database