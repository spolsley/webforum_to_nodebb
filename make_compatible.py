import pickle
from Mongo import Mongo

mon = pickle.load(open('output_final.pkl','rb'))

# convert mongo object into lists, pickle those, and that should load in python2
users = list(mon.m_users.values())
users_supp = mon.m_users_supp

topics = list(mon.m_topics.values())
topics_supp = mon.m_topics_supp

posts = list(mon.m_posts.values())
posts_supp = mon.m_posts_supp

all_data = [users,users_supp,topics,topics_supp,posts,posts_supp]

with open('output_compatible.pkl','wb') as pfile:
	pickle.dump(all_data,pfile,protocol = 2)