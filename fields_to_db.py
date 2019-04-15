import pickle
from urllib import quote_plus
from pymongo import MongoClient

mon = pickle.load(open('output_compatible.pkl','rb'))

username = quote_plus('<mongo admin user>')
password = quote_plus('<mongo admin pass>')
conn = MongoClient('mongodb://%s:%s@127.0.0.1' % (username,password)) # if running on server, else you'll need permissions to connect another address in Mongo
db = conn['<nodebb destination database>'] # database where your NodeBB instance is stored
coll = db['objects']

result = coll.insert_many(mon[0]) # users
result = coll.insert_many(mon[1]) # user supplemental
result = coll.insert_many(mon[2]) # topics
result = coll.insert_many(mon[3]) # topics supplemental
result = coll.insert_many(mon[4]) # posts
result = coll.insert_many(mon[5]) # posts supplemental
