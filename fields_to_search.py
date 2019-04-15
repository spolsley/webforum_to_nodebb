import pickle
from urllib import quote_plus
from pymongo import MongoClient

mon = pickle.load(open('output_compatible.pkl','rb'))

username = quote_plus('<mongo admin user>')
password = quote_plus('<mongo admin pass>')
conn = MongoClient('mongodb://%s:%s@127.0.0.1' % (username,password)) # if running on server, else you'll need permissions to connect another address in Mongo
db = conn['<nodebb destination database>'] # database where your NodeBB instance is stored
coll_posts = db['searchpost']
coll_topics = db['searchtopic']

searchposts = []
searchtopics = []

# build up search topics
for t in mon[2]:
    new_st = {
        'id':t['tid'],
        'cid':str(t['cid']),
        'uid':str(t['uid']),
        'content':t['title']
    }
    searchtopics.append(new_st)

# build up search posts
for p in mon[4]:
    tid = p['tid']
    for t in mon[2]:
        if t['tid'] == tid:
            cid = t['cid']
            break
    searchposts.append({'id':p['pid'],'cid':str(cid),'content':p['content'],'uid':str(p['uid'])})

result = coll_topics.insert_many(searchtopics) # topics
result = coll_posts.insert_many(searchposts) # posts
