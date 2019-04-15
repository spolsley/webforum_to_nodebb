import re

# could also be called NodeBB
# this class generates JSON docs for use with MongoDB in a NodeBB setup
class Mongo:
	def __init__(self):
		self.m_users = {}
		self.m_users_ord = []
		self.m_users_supp = []
		self.m_topics = {}
		self.m_topics_ord = []
		self.m_topics_supp = []
		self.m_posts = {}
		self.m_posts_ord = []
		self.m_posts_supp = []
		self.temp_topics = {} # sanity check, save expected or temp info for topics
		self.temp_posts = {} # likewise, save temp info for posts
		self.uid = 5 # starting user, topic, and post ids, probably no more than 1 or 2 in a new setup but may need to adjust if not new
		self.tid = 10
		self.pid = 20

	# manages user facets but doesn't do email and password currently
	def manage_user(self,username,joindate,postdate): # pass in timestamp * 1000 since need javascript (ms)
		if username not in self.m_users: # new user
			userslug_fixed = re.sub('[^a-zA-Z0-9_]', '-', username)
			new_user = {
				"_key" : "user:" + str(self.uid),
				"acceptTos" : 0,
				"banned" : 0,
				"birthday" : "",
				"email" : "",
				"fullname" : "",
				"gdpr_consent" : 1,
				"joindate" : joindate, # user timestamps updated by this function
				"lastonline" : postdate,
				"lastposttime" : postdate,
				"location" : "",
				"picture" : "",
				"postcount" : 0, # postcount will update in posts as added
				"profileviews" : 0,
				"reputation" : 0,
				"signature" : "",
				"status" : "online",
				"topiccount" : 0, # will update in topics as added
				"uid" : self.uid,
				"uploadedpicture" : "",
				"username" : username + "_bot", # username has _bot appended by default to differentiate imported users; it can be removed here
				"userslug" : userslug_fixed.lower() + "_bot",
				"website" : "",
				"password" : "",
				"passwordExpiry" : 0
			}
			self.m_users[username] = new_user
			self.m_users_ord.append(username)

			self.m_users_supp.append({"_key":"username:uid","value":username + "_bot","score":self.uid})
			self.m_users_supp.append({"_key":"userslug:uid","value":userslug_fixed.lower() + "_bot","score":self.uid})
			self.m_users_supp.append({"_key":"username:sorted","value":userslug_fixed.lower() + "_bot:" + str(self.uid),"score":0})
			self.m_users_supp.append({"_key":"group:registered-users:members","value":str(self.uid),"score":joindate})
			self.m_users_supp.append({"_key":"user:"+str(self.uid)+":usernames","value":username + "_bot","score":joindate})
			self.m_users_supp.append({"_key":"users:reputation","value":str(self.uid),"score":0})
			# ones to update
			self.m_users_supp.append({"_key":"users:joindate","value":str(self.uid),"score":joindate})
			self.m_users_supp.append({"_key":"users:postcount","value":str(self.uid),"score":0})

			self.uid += 1
		else: # existing user
			temp_uid = self.m_users[username]['uid'] # uid of existing user
			if self.m_users[username]['joindate'] > joindate: # update joindate if earlier one found
				self.m_users[username]['joindate'] = joindate
				for i in range(0,len(self.m_users_supp)): # in supplemental list as well
					if self.m_users_supp[i]['value'] == str(temp_uid) and self.m_users_supp[i]['_key'] == "users:joindate":
						self.m_users_supp[i]['score'] = joindate
			if self.m_users[username]['lastposttime'] < postdate: # update postdate if later one found
				self.m_users[username]['lastposttime'] = postdate
				self.m_users[username]['lastonline'] = postdate


	# manage topic facets, really only needs to update as posts added and teaser post on original object
	def manage_topic(self,tid,cid,creator,timestamp,title,views,description,posts,link,lastposttime,lastpostby):
		self.manage_user(creator,timestamp,timestamp) # ensure user exists and has up-to-date info
		uid = self.m_users[creator]['uid'] # user id will be one assigned in user list
		if tid not in self.m_topics: # new topic, stored by old id
			topicslug_fixed = re.sub('[^a-zA-Z0-9_]', '-', title)
			new_topic = {
				"_key" : "topic:" + str(self.tid),
				"cid" : cid,
				"deleted" : 0,
				"lastposttime" : timestamp, # will update when any post added
				"locked" : 0,
				"mainPid" : 0, # will update when first post added
				"pinned" : 0,
				"postcount" : 0, # will update when any post added
				"slug" : str(self.tid)+"/"+topicslug_fixed.lower(), # slug uses dashes not spaces
				"tid" : self.tid,
				"timestamp" : timestamp,
				"title" : title,
				"uid" : uid,
				"viewcount" : views,
				"teaserPid" : 0 # will update when any post added
			}
			self.m_topics[tid] = new_topic
			self.m_topics_ord.append(tid)

			self.temp_topics[tid] = {
				"description": description,
				"posts": posts,
				"link": link,
				"lastposttime": lastposttime,
				"lastpostby": lastpostby
			}

			# update user info
			self.m_topics_supp.append({"_key":"uid:"+str(uid)+":topics","value":str(self.tid),"score":timestamp})
			self.m_users[creator]['topiccount'] += 1

			self.m_topics_supp.append({"_key":"topics:tid","value":str(self.tid),"score":timestamp})
			self.m_topics_supp.append({"_key":"cid:"+str(cid)+":tids","value":str(self.tid),"score":timestamp})
			self.m_topics_supp.append({"_key":"cid:"+str(cid)+":tids:votes","value":str(self.tid),"score":0})
			self.m_topics_supp.append({"_key":"cid:"+str(cid)+":uid:"+str(uid)+":tids","value":str(self.tid),"score":timestamp})

			# ones will be updated as posts added
			self.m_topics_supp.append({"_key":"cid:"+str(cid)+":tids:lastposttime","value":str(self.tid),"score":timestamp})
			self.m_topics_supp.append({"_key":"cid:"+str(cid)+":tids:posts","value":str(self.tid),"score":0})
			self.m_topics_supp.append({"_key":"topics:recent","value":str(self.tid),"score":timestamp})
			self.m_topics_supp.append({"_key":"topics:posts","value":str(self.tid),"score":0})

			self.tid += 1


	# manage post facets, influences others as well
	def manage_post(self,pid,tid,author,timestamp,content,reply,num,link):
		self.manage_user(author,timestamp,timestamp) # ensure user exists and has up-to-date info
		uid = self.m_users[author]['uid'] # uid from new user, not old id needed
		# assume topic has been created
		new_tid = self.m_topics[tid]['tid'] # tid from new topic, not old id
		cid = self.m_topics[tid]['cid'] # get cid from new topic, so no need to pass any forum ids
		if pid not in self.m_posts: # new post, stored by old id
			new_post = {
				"_key" : "post:"+str(self.pid),
				"content" : content,
				"deleted" : 0,
				"pid" : self.pid,
				"tid" : new_tid,
				"timestamp" : timestamp,
				"uid" : uid,
				"replies" : 0 # will update with any reply
			}
			if reply > 0: # handle reply info
				new_post['toPid'] = self.m_posts[reply]['pid'] # set reply pid to new id from original id
				self.m_posts[reply]['replies'] += 1 # update reply count on original
				self.m_posts_supp.append({"_key":"pid:"+str(self.m_posts[reply]['pid'])+":replies","value":str(self.pid),"score":timestamp})
			self.m_posts[pid] = new_post
			self.m_posts_ord.append(pid)

			self.temp_posts[pid] = {
				"num": num,
				"link": link
			}

			# update user info
			self.m_posts_supp.append({"_key":"uid:"+str(uid)+":posts","value":str(self.pid),"score":timestamp})
			self.m_users[author]['postcount'] += 1

			for i in range(0,len(self.m_users_supp)): # increment user post count
				if self.m_users_supp[i]['value'] == str(uid) and self.m_users_supp[i]['_key'] == "users:postcount":
					self.m_users_supp[i]['score'] += 1

			# update topic info
			if self.m_topics[tid]['mainPid'] == 0: # adding first post
				self.m_topics[tid]['mainPid'] = self.pid
			else: # other posts added with supplemental
				self.m_posts_supp.append({"_key":"tid:"+str(new_tid)+":posts","value":str(self.pid),"score":timestamp})
				self.m_posts_supp.append({"_key":"tid:"+str(new_tid)+":posts:votes","value":str(self.pid),"score":0})
			self.m_topics[tid]['teaserPid'] = self.pid
			self.m_topics[tid]['lastposttime'] = timestamp
			self.m_topics[tid]['postcount'] += 1

			foundPoster = False
			for i in range(0,len(self.m_topics_supp)): # incremenet topic post count and timestamps
				if self.m_topics_supp[i]['value'] == str(new_tid) and self.m_topics_supp[i]['_key'] == "cid:"+str(cid)+":tids:lastposttime":
					self.m_topics_supp[i]['score'] = timestamp
				if self.m_topics_supp[i]['value'] == str(new_tid) and self.m_topics_supp[i]['_key'] == "cid:"+str(cid)+":tids:posts":
					self.m_topics_supp[i]['score'] += 1
				if self.m_topics_supp[i]['value'] == str(new_tid) and self.m_topics_supp[i]['_key'] == "topics:recent":
					self.m_topics_supp[i]['score'] = timestamp
				if self.m_topics_supp[i]['value'] == str(new_tid) and self.m_topics_supp[i]['_key'] == "topics:posts":
					self.m_topics_supp[i]['score'] += 1
				if self.m_topics_supp[i]['_key'] == "tid:"+str(new_tid)+":posters" and self.m_topics_supp[i]['value'] == str(uid):
					self.m_topics_supp[i]['score'] += 1
					foundPoster = True
			if not foundPoster:
				self.m_topics_supp.append({"_key":"tid:"+str(new_tid)+":posters","value":str(uid),"score":1})

			self.m_posts_supp.append({"_key":"posts:pid","value":str(self.pid),"score":timestamp})
			self.m_posts_supp.append({"_key":"cid:"+str(cid)+":pids","value":str(self.pid),"score":timestamp})

			self.pid += 1

