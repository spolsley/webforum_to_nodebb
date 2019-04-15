from urllib import quote_plus
import re
from pymongo import MongoClient

username = quote_plus('<mongo admin user>')
password = quote_plus('<mongo admin pass>')
conn = MongoClient('mongodb://%s:%s@127.0.0.1' % (username,password)) # if running on server, else you'll need permissions to connect another address in Mongo
db = conn['<nodebb destination database>'] # database where your NodeBB instance is stored
objs = db['objects']

names = objs.find({'_key':'username:sorted'})

for name in names:
    old = name['value']
    new_start = old[0:old.rfind(':')] # split at last ':' to get name from uid
    new_start_fixed = re.sub('[^a-zA-Z0-9_]', '-', new_start).lower()
    new_final = new_start_fixed + old[old.rfind(':'):len(old)]
    objs.update_one({'_id':name['_id']},{'$set':{'value':new_final}},upsert=False)
