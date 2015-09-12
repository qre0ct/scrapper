# there is an awesome python wrapper (called PRAW) around the standard reddit APIs. So we are just gonna make use of it. 

import datetime
import praw

r = praw.Reddit(user_agent='olaCabs_social_monitor')
submissions = r.search("ola cabs", limit=10)
for x in submissions:
	message = str(x)[(str(x).find(": ") + 2) :] + " & the link is " + str(x.short_link)
	time = x.created
	ts = datetime.datetime.fromtimestamp(time)
	message = message + " at " + str(ts)
	print message