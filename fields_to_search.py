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
print "Processing " + str(len(mon[2])) + " topics..."
for t in mon[2]:
    new_st = {
        'id':t['tid'],
        'cid':str(t['cid']),
        'uid':str(t['uid']),
        'content':t['title']
    }
    searchtopics.append(new_st)

print "Topics Ready"

# build up search posts
count = 0
print "Processing " + str(len(mon[4])) + " posts..."
for p in mon[4]:
    tid = p['tid']
    for t in mon[2]:
        if t['tid'] == tid:
            cid = t['cid']
            break
    count += 1
    searchposts.append({'id':p['pid'],'cid':str(cid),'content':p['content'],'uid':str(p['uid'])})
    if count % 1000:
        print count

print "Posts Ready"

print "Inserting Topics"
result = coll_topics.insert_many(searchtopics) # topics
print "Inserting Posts"
result = coll_posts.insert_many(searchposts) # posts
print "Done"
