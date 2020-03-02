import pickle
from urllib import quote_plus
from pymongo import MongoClient

mon = pickle.load(open('output_compatible.pkl','rb'))

username = quote_plus('<mongo admin user>')
password = quote_plus('<mongo admin pass>')
conn = MongoClient('mongodb://%s:%s@127.0.0.1' % (username,password)) # if running on server, else you'll need permissions to connect another address in Mongo
db = conn['<nodebb destination database>'] # database where your NodeBB instance is stored
coll = db['objects']

coll.insert_many(mon[0])
print "Inserted users"

for el in mon[1]: # user supp has some key issue so just let it skip the ones that don't work
	try:
		coll.insert_one(el)
	except Exception as e:
		print e
print "Inserted User Information"

coll.insert_many(mon[2])
print "Inserted Topics"
coll.insert_many(mon[3])
print "Inserted Topic Information"
coll.insert_many(mon[4])
print "Inserted Posts"
coll.insert_many(mon[5])
print "Inserted Post Information"
