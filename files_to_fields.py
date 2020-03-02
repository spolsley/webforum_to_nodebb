from bs4 import BeautifulSoup
import urllib3
import urllib.parse as urlparse
from datetime import datetime
import time
import re
import html2text
from Mongo import Mongo
import pickle

# import pdb
# pdb.set_trace()

# setup smiley mapping, very simple approach just replace with text
emoticon = {
	'wink.gif' : ';)',
	'tongue.gif' : ':p',
	'heythere.gif' : ':heythere:',
	'sad.gif' : ':(',
	'smile.gif' : ':)',
	'rolleyes.gif' : ':rolleyes:',
	'biggrin.gif' : ':D',
	'eek.gif' : ':eek:',
	'mad.gif' : ':mad:',
	'cool.gif' : ':cool:',
	'frown.gif' : ':frown:',
	'confused.gif' : ':confused:',
	'redface.gif' : ':redface:',
	'unsure.gif' : ':unsure:',
	'ohmy.gif' : ':o',
	'happy.gif' : '^_^',
	'ph34r.gif' : ':ninja:',
	'laugh.gif' : ':laugh:',
	'blink.gif' : ':blink:',
	'huh.gif' : ':huh:',
	'sleep.gif' : '-_-',
	'wub.gif' : ':wub:',
	'dry.gif' : '<_<',
	'wacko.gif' : ':wacko:',
	'hector.gif' : ':hector_bird:',
	'duh.gif' : ':duh:',
	'mellow.gif' : ':mellow:',
	'blush.gif' : ':blush:',
	'despair.gif' : ':despair',
	'thumbsdown.gif' : ':thumbsdown:',
	'leno.gif' : ':leno:',
	'gasp.gif' : ':o'
}

# setup html2markdown
md_handler = html2text.HTML2Text()
md_handler.body_width = 0

# setup mongo client for creating and storing fields
mon = Mongo()
category = 6 # destination forum num, 6 for cythera web and 7 for chronicles

# setup crawler to reuse same connection
# http = urllib3.PoolManager()

# use list as stack to visit pages in following order:
# add topics, then topic next link, then forum next page link
# on a stack, visits all forum pages, then all topic pages, and all topics in reverse order (starts at oldest essentially)
url_stack = []

# Load from "crawl.txt" file list
# with open('crawl.txt') as f:
# 	for line in f:
# 		if not line.strip() == '':
# 			url_stack.append(line.strip())

# seed forums and urls
forums = {}
forums[17] = 'http://www.ambrosiasw.com/forums/index.php?showforum=17&prune_day=100&sort_by=Z-A&sort_key=last_post&topicfilter=all&st=0'
forums[64] = 'http://www.ambrosiasw.com/forums/index.php?showforum=64&prune_day=100&sort_by=Z-A&sort_key=last_post&topicfilter=all&st=0'

forum_stats = []

# testing
# forums = {}
# forums[17] = 'http://www.ambrosiasw.com/forums/index.php?showtopic=6062'

## Category mapping
cat_map = {
17  : 7, # >  |---- Cythera web board
64  : 6  # >  |---- Cythera Chronicles
}

link_tracker = open('links.txt','w')
topic_stack = [] # keep topics in stack to add in correct order (reading from latest but then visit last)

for forum in forums:
	print("Forum #: " + str(forum))
	forum_tids = 0
	forum_pids = 0
	url_stack.append(forums[forum]) # seed url
	# change destination category based on mapping from old to new
	category = cat_map[forum]

	# while links to visit
	while len(url_stack) > 0:
		print(str(len(url_stack)))
		try:
			next_url = url_stack.pop()

			# in this file, we won't make a request, we'll load from the file store
			# get html file
			parsed = urlparse.urlparse(next_url)
			args = urlparse.parse_qs(parsed.query)
			if 'showforum' in args:
				page = int(int(args['st'][0]) / 30) # page number is divisble by 30 for forum topic lists (default shows 30 topics per page)
				soup = BeautifulSoup(open("data/f" + str(forum) + "_p" + str(page) + ".html"), 'html.parser')
				if not soup.body:
					soup = BeautifulSoup(open("data/f" + str(forum) + "_p" + str(page) + ".html"), 'lxml') # try with different parser
			elif 'showtopic' in args:
				topicnum = int(args['showtopic'][0])
				if 'st' in args:
					page = int(int(args['st'][0]) / 25) # page number is divisible by 25 for topic posts (default shows 25 posts per page)
				else:
					page = 0
				soup = BeautifulSoup(open("data/f" + str(forum) + "_t" + str(topicnum) +  "_p" + str(page) + ".html"), 'html.parser')
				if not soup.body:
					soup = BeautifulSoup(open("data/f" + str(forum) + "_t" + str(topicnum) +  "_p" + str(page) + ".html"), 'lxml') # try with different parser
			else:
				page = -1
				print("Failed to load url: " + next_url)

			# If forum page, add topic links to process and extract fields for mongo
			all_topics = soup.body.find('table',attrs={'class':'topic_list'})
			if all_topics:
				topics_inserted = 0
				all_topics_list = [x for x in all_topics.children]

				# From table listing all topics, find which entries are actually topics
				for topic in all_topics_list:
					try:
						checking = [x for x in topic.children]
						if len(checking) > 3:
							if len(checking[3].find('a',attrs={'class':'topic_title'})) > 0: # find topic entry if possible
								# Each row is a collection of relevant info
								topic_info = [x for x in topic.children]

								# 3rd child is column with name and description in indices 7 and 12
								temp = [x for x in topic_info[3].children]
								topic_title = topic.find('a',attrs={'class':'topic_title'}).text.strip()
								topic_link = topic.find('a',attrs={'class':'topic_title'})['href']
								topic_started_str = topic.find('a',attrs={'class':'topic_title'})['title']
								topic_started_str = topic_started_str.replace("View topic, started", "").strip()
								topic_started_date = datetime.strptime(topic_started_str,"%d %B %Y - %I:%M %p")
								topic_started = time.mktime(topic_started_date.timetuple())
								temp = topic.find('span',attrs={'class':'desc'})
								if temp:
									topic_desc = temp.text.strip()
								else:
									topic_desc = ''

								# 5th child has the author name
								topic_author = topic_info[5].text.strip()

								# 7th child is column with reply and view counts nested in 1st child at indices 1 and 3
								temp = [y for y in [x for x in topic_info[7].children][1].children]
								topic_replies = int(temp[1].text.strip().split(" ")[0].replace(",","")) # parse into int by removing commas from #
								topic_views = int(temp[3].text.strip().split(" ")[0].replace(",",""))

								# 9th child is last poster and last post time nested in 1st child at indices 1 and 3
								temp = [y for y in [x for x in topic_info[9].children][1].children]
								temp_date = temp[1].text.strip() # string date
								temp_date = datetime.strptime(temp_date,'%b %d %Y %I:%M %p') # datetime date
								topic_lastpost = time.mktime(temp_date.timetuple()) # timestamp date
								topic_lastpostby = temp[3].text.strip().split(' ')[1]

								# topic id from url
								topic_parsed = urlparse.urlparse(topic_link)
								topic_args = urlparse.parse_qs(topic_parsed.query)
								if 'showtopic' in topic_args:
									topic_id = int(topic_args['showtopic'][0])

								if topic_replies >= 0: # ignore empty topics (-1 for deleted)
									url_stack.append(topic_link)
									topics_inserted += 1
									forum_tids += 1
									# if topic inserted, also add to the list of mongo fields
									topic_stack.append([topic_id,category,topic_author,topic_started*1000,topic_title,topic_views,topic_desc,topic_replies,topic_link,topic_lastpost*1000,topic_lastpostby])
								else:
									print("Not adding topic " + topic_title + " on page " + str(page))

								# print(topic_title,topic_desc,topic_author,str(topic_replies),str(topic_views),str(topic_lastpost),topic_lastpostby)
					except:
						pass # really don't care if it fails, likely a row of no interest

				print("Inserted " + str(topics_inserted) + " on page " + str(page))
			
			posts_counted = 0
			# if topic, process all posts, extracting fields for users and posts docs in mongodb
			all_posts = soup.body.find('div',attrs={'class':'topic'})
			if all_posts:
				while len(topic_stack) > 0: # before processing posts, empty all topics on stack
					tc = topic_stack.pop()
					mon.manage_topic(tc[0],tc[1],tc[2],tc[3],tc[4],tc[5],tc[6],tc[7],tc[8],tc[9],tc[10])
				topic_id = topicnum # simplify nomenclature and use topic_id for id (same as topicnum when parsing posts)
				posts_parent = all_posts.find('span',attrs={'class':'main_topic_title'}).text.strip()

				# check if poll present
				poll = all_posts.find('div',attrs={'class':'poll'})
				if poll:
					poll_text_raw = poll.text
					# remove debug and ending info
					poll_text_short = poll_text_raw[0:poll_text_raw.find('Debug.dir( ipb.topic.poll )')]
					poll_text = re.sub(r'\n+','\n',re.sub(r'\t+','\t',poll_text_short))
				# for post in all_posts.findAll('div',attrs={'class':'post_block'}): # works for almost all topics and posts, a few with html issues can't be fully parsed by bs4
				for post in soup.findAll('div',attrs={'class':'post_block'}): # already checked if posts (from if all_post), so just grab all post blocks, may lose a few lines here or there from broken html
					try:
						# author name
						guest = post.find('h3',attrs={'class':'guest'})
						if guest:
							post_author = re.sub(r"#[0-9]*","",guest.text.strip()).strip() # guest.text gets guest name and post id, so use regex to remove id
						else:
							post_author = post.find('span',attrs={'class':'author'}).text.strip()
						# join date
						author_joined = 0 # start with 0, will set later
						for el in post.find('ul',attrs={'class':'user_fields'}).children:
							try:
								if el.find('span',attrs={'class':'ft'}).text.strip() == 'Joined:':
									author_joined_str = el.find('span',attrs={'class':'fc'}).text.strip()
									author_joined_date = datetime.strptime(author_joined_str,'%d-%B %y')
									author_joined = time.mktime(author_joined_date.timetuple()) # set here if available
									break
							except:
								pass # ignore non-join date entries

						# post date
						post_date_str = post.find('abbr',attrs={'class':'published'}).text.strip()
						try:
							post_date_date = datetime.strptime(post_date_str,'%d %B %Y - %I:%M %p')
							post_date = time.mktime(post_date_date.timetuple())
						except:
							pass # just use the last valid post date if none can be extracted from this post (can happen due to errors in the original forum)

						# post num and id (num in topic, id is global)
						post_info = post.find('a',attrs={'rel':'bookmark'})
						postnum = int(post_info.text.strip().replace('#',''))
						post_link = post_info['href']
						post_parsed = urlparse.urlparse(post_link)
						post_args = urlparse.parse_qs(post_parsed.query)
						if 'p' in post_args:
							post_id = int(post_args['p'][0])

						# post content
						post_content = post.find('div',attrs={'class':'entry-content'})
						# in content, determine if reply and which post replying to and make sure syntax for quote/reply correct in body
						post_replyto = -1 # default not reply
						snapback = post_content.find('a',attrs={'rel':'citation'})
						if snapback:
							snapback_link = snapback['href']
							snapback_parsed = urlparse.urlparse(snapback_link)
							snapback_args = urlparse.parse_qs(snapback_parsed.query)
							if 'pid' in snapback_args:
								temp_post_replyto = int(snapback_args['pid'][0])
								try: # can only set reply link if same topic for nodebb
									reply_tid = mon.m_posts[temp_post_replyto]['tid']
									if reply_tid == mon.m_topics[topic_id]['tid']:
										post_replyto = temp_post_replyto # set replyto post id if available
								except:
									pass
								
						# translate from html to markdown (bb code was already translated to html for website, which this pulls from)
						post_content_text = str(post_content)
						post_content_text = post_content_text.replace('[','(').replace(']',')') # first, remove square brackets
						post_md = md_handler.handle(post_content_text)

						# adjust post contents with other info
						if postnum == 1: # first post
							# add topic if missed for some reason (really only useful in testing since won't do anything in general usage, unless a bug)
							mon.manage_topic(topic_id,category,post_author,post_date*1000,posts_parent,0,'',0,'',post_date*1000,post_author)
							# add poll information on top, if available
							if poll:
								post_md = poll_text + '\n\n' + post_md
							# add topic description at very topic, if available (will be empty string if not)
							topic_desc = mon.temp_topics[topic_id]['description']
							if len(topic_desc) > 0:
								post_md = "**" + topic_desc + "**\n\n" + post_md

						# replyto link points to first found reply (if in same topic), but must update any citation links in text to appropriate post
						snapback = post_content.findAll('a',attrs={'rel':'citation'})
						if snapback:
							original_posts = []
							for citation in snapback:
								citation_link = citation['href']
								citation_parsed = urlparse.urlparse(citation_link)
								citation_args = urlparse.parse_qs(citation_parsed.query)
								if 'pid' in citation_args:
									original_posts.append(int(citation_args['pid'][0])) # keep list of originals if necessary
							lookfor = '[![View Post](http://www.ambrosiasw.com/forums/public/style_images/ipb23/snapback.png)'
							while post_md.find(lookfor) >= 0 and len(original_posts) > 0:
								temp_md = post_md[post_md.find(lookfor):len(post_md)] # substring from current quote to end
								old_user_stoppoint = temp_md.find(',')
								to_replace = post_md[post_md.find(lookfor):post_md.find(lookfor)+old_user_stoppoint]
								# attempt to replace, should work if the post is on cythera boards
								try:
									old_id = original_posts.pop(0)
									new_id = mon.m_posts[old_id]['pid']
									new_user_id = mon.m_posts[old_id]['uid']
									new_topic_id = mon.m_posts[old_id]['tid']
									for k,v in mon.m_users.items():
										if v['uid'] == new_user_id:
											new_username = v['userslug']
											break
									for k,v in mon.m_topics.items():
										if v['tid'] == new_topic_id:
											new_topicname = v['title']
											break
									post_md = post_md.replace(to_replace,'@'+new_username,1)
									post_md = post_md.replace('said:\n\n','said in ['+new_topicname+'](/post/'+str(new_id)+'):\n> ',1)
								except:
									pass # no need to replace if not easy to do

						all_links = re.findall(r"((?:__|[*#])|!?\[(.*?)\]\(.*?\))",post_md)
						for l in all_links:
							split_l = l[0].split('/')
							last_l = split_l[len(split_l)-1]
							last_l = last_l.replace(')','')
							if last_l in emoticon: # handle known ones
								post_md = post_md.replace(l[0],emoticon[last_l])
							elif '*' == l[0] or '#' == l[0] or '__' == l[0]: # ignore unexpected matches
								pass
							else: # save anything unknown to link tracker
								link_tracker.write(l[0])
								link_tracker.write('\n')

						# add to fields list in mongo handler
						mon.manage_user(post_author,author_joined*1000,post_date*1000)
						mon.manage_post(post_id,topic_id,post_author,post_date*1000,post_md,post_replyto,postnum,post_link)

						posts_counted += 1
						forum_pids += 1

					except:
						print("Skipping post " + str(posts_counted) + " in topic " + str(topicnum) + " forum " + str(forum))

			# if forum page or topic, add next link if available to process next
			next_link = soup.body.find('a',attrs={'title':'Next page','rel':'next'})
			if next_link:
				url_stack.append(next_link['href'])
				# if there's a next page, check that all 25 posts have been counted
				if posts_counted > 0: # must have been a page with posts
					if posts_counted < 25:
						print("Missed " + str(25-posts_counted) + " post(s) on topic " + str(topicnum))
		except:
			print("Exception occurred! Saving current crawl list to file.")
			url_stack.append(next_url) # place failed one back on stack
			with open("crawl.txt","w") as output:
				for url in url_stack:
					output.write(url)
					output.write("\n")
			print("File saved. Trying again.")
	forum_stats.append([category,forum_tids,forum_pids])

pickle.dump(mon,open('output.pkl','wb'),pickle.HIGHEST_PROTOCOL)

with open('stats.txt','w') as statfile:
	for stat in forum_stats:
		statfile.write("c: " + str(stat[0]) + " t: " + str(stat[1]) + " p: " + str(stat[2]))
		statfile.write("\n")
	statfile.write("Overall:\n")
	statfile.write("Topics: " + str(mon.tid) + " Posts: " + str(mon.pid) + " Users: " + str(mon.uid))

link_tracker.close()

