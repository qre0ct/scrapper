# playing with the twitter API
from TwitterSearch import *
try:
	tso = TwitterSearchOrder() # create a TwitterSearchOrder object
	tso.set_keywords(['olastore']) # let's define all words we would like to have a look for
	tso.set_include_entities(False) # and don't give us all those entity information


	# it's about time to create a TwitterSearch object with our secret tokens
	ts = TwitterSearch(
		consumer_key = 'RLXY0g7xiLLs0zbU21QQd1neH',
		consumer_secret = 'c8NgW92oYjyOZfyNwRQjXSkasF0Cv3wGIO4dsjl2RyOCYZ3HzT',
		access_token = '3433982414-6p8ccwItkWO2GF90YiUIS30o6U3Fy10T50TouRB',
		access_token_secret = 'ZDY7QbfBZ1uvLjzjlF7A4zZxMSNgmoJo6qsbuuhlPAAPM'
	 )

	 # this is where the fun actually starts :)
	for tweet in ts.search_tweets_iterable(tso):
		print "@" + str((tweet['user']['screen_name']).encode("utf-8")) + " tweeted " + str(tweet['text'].encode("utf-8")) + "and the time was " + str(tweet['created_at'].encode("utf-8")) + " and the id of the tweet is " + str(tweet['id'])
	print "\n\n"
except TwitterSearchException as e: # take care of all those ugly errors if there are some
	print(e)