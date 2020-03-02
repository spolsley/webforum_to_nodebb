from bs4 import BeautifulSoup
import urllib3
import urllib.parse as urlparse
from datetime import datetime
import time

#import pdb
#pdb.set_trace()

# setup crawler to reuse same connection
http = urllib3.PoolManager()

# use list as stack to visit pages in following order:
# add topics, then topic next link, then forum next page link
# on a stack, visits all forum pages, then all topic pages, and all topics in reverse order (starts at oldest essentially)
url_stack = []

# Load from "crawl.txt" file list if preferred, e.g. last crawl failed or placed start urls in "crawl.txt"
# with open('crawl.txt') as f:
# 	for line in f:
# 		if not line.strip() == '':
# 			url_stack.append(line.strip())

# saved failed pages
crawl_stat_log = open('crawl_log.txt','a+')

url_fails = 0

# seed forums and urls
forums = {}

# Cythera web board (17)
forums[17] = 'http://www.ambrosiasw.com/forums/index.php?showforum=17&prune_day=100&sort_by=Z-A&sort_key=last_post&topicfilter=all&st=0'


# Cythera Chronicles (64)
forums[64] = 'http://www.ambrosiasw.com/forums/index.php?showforum=64&prune_day=100&sort_by=Z-A&sort_key=last_post&topicfilter=all&st=0'


for forum in forums:
	url_stack.append(forums[forum]) # seed url

	# while links to visit
	while len(url_stack) > 0:
		print(str(len(url_stack)))
		try:
			next_url = url_stack.pop()

			# get html data
			response = http.request('GET',next_url,preload_content=False)
			soup = BeautifulSoup(response.data,'html.parser')

			# save html to file (named accordingly)
			parsed = urlparse.urlparse(next_url)
			args = urlparse.parse_qs(parsed.query)
			if 'showforum' in args:
				page = int(int(args['st'][0]) / 30) # page number is divisble by 30 for forum topic lists (default shows 30 topics per page)
				with open("data/f" + str(forum) + "_p" + str(page) + ".html", "w") as output:
					output.write(str(soup))
			elif 'showtopic' in args:
				topicnum = int(args['showtopic'][0])
				if 'st' in args:
					page = int(int(args['st'][0]) / 25) # page number is divisible by 25 for topic posts (default shows 25 posts per page)
				else:
					page = 0
				with open("data/f" + str(forum) + "_t" + str(topicnum) +  "_p" + str(page) + ".html", "w") as output:
					output.write(str(soup))
			else:
				page = -1
				print("Failed to save url: " + next_url)
				crawl_stat_log.write("Failed to save url: " + next_url)
				crawl_stat_log.write('\n')

			# If forum page, add topic links
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

								if topic_replies >= 0: # ignore empty topics (-1 for deleted)
									url_stack.append(topic_link)
									topics_inserted += 1
								else:
									crawl_stat_log.write("Not adding topic " + topic_title + " on page " + str(page))

								# print(topic_title,topic_desc,topic_author,str(topic_replies),str(topic_views),str(topic_lastpost),topic_lastpostby)
					except:
						pass # really don't care if it fails, likely a row of no interest

				print("Inserted " + str(topics_inserted) + " on page " + str(page))
				crawl_stat_log.write("Inserted " + str(topics_inserted) + " on page " + str(page))
				crawl_stat_log.write('\n')

			# if forum page or topic, add next link if available
			next_link = soup.body.find('a',attrs={'title':'Next page','rel':'next'})
			if next_link:
				url_stack.append(next_link['href'])
		except:
			print("Exception occurred! Saving current crawl list to file, moving on.")
			crawl_stat_log.write("Exception occurred! Saving current crawl list to file, moving on.\n")
			if url_fails < 3:
				url_fails += 1 # increment so eventually will stop trying this url
				url_stack.append(next_url) # save failed one back to stack (could cause it to endlessly loop without fail counter)
			else:
				crawl_stat_log.write('Exception occurred with url at least 3 times: ' + next_url) # save failed one to output
				crawl_stat_log.write('\n')
				url_fails = 0 # don't replace on stack, just log and reset count for next url
			with open("crawl.txt","w") as output:
				for url in url_stack:
					output.write(url)
					output.write("\n")
			print("File saved. Trying again.")
			crawl_stat_log.write("File saved. Trying again.\n")

crawl_stat_log.close()
