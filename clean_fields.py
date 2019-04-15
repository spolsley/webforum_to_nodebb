from Mongo import Mongo
import pickle
import re

# import pdb
# pdb.set_trace()

with open('output.pkl','rb') as toclean:
	mon = pickle.load(toclean)

link_cleaner = open('links.txt','w')

# first, set all topics to locked since it's easier to unlock as needed
# for k in mon.m_topics:
# 	mon.m_topics[k]['locked'] = 1

# goal of cleaning is to remove old links and make as many internal links as possible
# must be done after initial processing because linking order is not guaranteed for all info
# we cleaned in-topic replies and existing posts, plus smileys, as much as possible; now handle any remaining inter-linking
for k in mon.m_posts:
	content = mon.m_posts[k]['content']

	# remove leftovers from invalid replies to just turn into standard links
	lookfor = '![View Post](http://www.ambrosiasw.com/forums/public/style_images/ipb23/snapback.png)'
	if lookfor in content:
		content = content.replace(lookfor,'View Post')

	# process all links
	all_links = re.findall(r"((?:__|[*#])|!?\[(.*?)\]\(.*?\))",content)
	for link in all_links:
		link_split = link[0].split(']')
		for ls in link_split:
			if ls[0] == '(': # find start of hyperlink
				hyperlink = ls[1:ls.find(')')]
				# handle hyperlinks in a simplistic way: if findpost, try to make post link; if showtopic, try to make topic link
				try:
					if 'findpost' in hyperlink: # look here first, then fall back on topic
						ids = hyperlink.split('=') # doing this way because there's so many variations, only findpost is shared
						pid = int(ids[-1].replace(')',''))
						new_pid = mon.m_posts[pid]['pid']
						content = content.replace(hyperlink,'/post/'+str(new_pid))
					elif 'showtopic' in hyperlink: # check for topic id second
						ids = hyperlink.split('=')
						tid = int(ids[-1].replace(')',''))
						new_pid = mon.m_topics[tid]['mainPid']
						content = content.replace(hyperlink,'/post/'+str(new_pid))
				except:
					pass # don't replace if not easy to do

	# go through links for verification
	all_links = re.findall(r"((?:__|[*#])|!?\[(.*?)\]\(.*?\))",content)
	for link in all_links:
		if '*' != link[0] and '#' != link[0] and '__' != link[0]: # ignore unexpected matches
			link_cleaner.write(link[0])
			link_cleaner.write('\n')

	# update post content
	mon.m_posts[k]['content'] = content

pickle.dump(mon,open('output_final.pkl','wb'),pickle.HIGHEST_PROTOCOL)
