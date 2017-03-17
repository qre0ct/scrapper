# Making the final integrated code that would call the scrappers for the different platforms. Trying to keep each it as modular as possible 
# to allow extensibility in terms of addition of more platforms later. 

''' Enhancements :
1. Make it multithreaded
2. Make it plagagabel
3. Write plugins 
4. Make it smarter in terms or reports... so maybe do some AI / NLP before reporting the results found
'''

__author__ = 'abhinav.chourasia'

##############################################################################################################################################
import requests
import json
import urllib
from bs4 import BeautifulSoup # for pasring pages in Pastebin and PastieGoogle
from configobj import ConfigObj
import datetime # for datetime function used in Reddit class
import dateutil # for normalizing timestamp of each post
from dateutil import parser # for normalizing timestamp of each post
import pytz # for normalizing timestamp of each post
import praw # reddit wrapper
from TwitterSearch import * # twitter wrapper
import hashlib # for hash calculation
from operator import itemgetter # for sorting the list of lists rowOfDataInDb as per the time stamp which is the 2nd element is each inner list
import MySQLdb as mdb # for DB interactions
import time # for strftime to convert the normalized time to a format that can be inserted in a datatime column in MySql
from warnings import filterwarnings # to supress MySql "warnings"
import smtplib # for mail notifications whenever there is a new entry in the db
##############################################################################################################################################

##############################################################################################################################################
# The class that holds the common methods required for scrapping. 
class ScrapeHelper():
	
	# ----------------------------------------------------------------------------------------------------------------------------------------
	def __init__(self):
		self.CONFIG_FILE = 'config.cfg'
		self.moreConfig = ConfigObj(self.CONFIG_FILE)
		self.searchKeyWords = self.moreConfig['keyword']['search_term']
		currentlySearchingFor = None

		self.timeStampHolder = []
		# initializing the first 3 indices of the list with none
		self.timeStampHolder.append(None)
		self.timeStampHolder.append(None)
		self.timeStampHolder.append(None)
		self.rowOfDataInDb = [] # is the list that finally gets checked for in the db and if does not exist it is added as a new row in it.
		self.utc = pytz.UTC
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# In certain cases where in an API provided by the platform is not being used to scrape and reather just their web search feature is being 
	# used we are manually extracting the time stamp of the post from the response page using the below method. 
	# In such cases the self.timeStampHolder list holds the exact section of the response page where in time of the post is displayed on the DOM
	# This may actually be entirely different for each platform and for now may even be the most idiotic solution possible out there ! 
	# YOU HAVE BEEN WARNED !!
	def extractPostTime(self, url):
		response = requests.get(url)
		#print response
		if (response.status_code == 200):
			#print response.text
			if(response.text.find(self.timeStampHolder[0])):
				#print "\nTime Stamp Found !"
				soup = BeautifulSoup(response.text, 'html.parser')

				if(soup):
					#print "\nHot Soup Ready "
					elms = soup.select(self.timeStampHolder[1])
					for i in elms:
						return str(i.attrs[self.timeStampHolder[2]])
				else:
					print "\nCould not make the soup !!"

			else:
				print "\n\nTime Stamp Not Found "
		else:
			print response.status_code
			print "\nNo response received\n\n"
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# accepts a platform, response of the search query in the respective platform and the timestamp when the post was done on that platform and cal-
	# culates the #. Then it updates all of these details as a list into self.rowOfDataInDb[].
	def prepareDbData(self, postedOn, thePostItself, postedAt):
		localList = []

		if(postedAt != "None"):
			# that is the result was not a Google search link
			# normalize the post time to a common format
			datetimeObj = parser.parse(postedAt)
			normalizedPostedAt = datetimeObj.replace(tzinfo=self.utc)

		else:
			# That it was a Google search result
			normalizedPostedAt = None

		# hash is being calculated on the following parameters
		appendedValues = postedOn + thePostItself + str(normalizedPostedAt)
		
		# calculating the hash
		hashObject = hashlib.sha1()
		hashObject.update(appendedValues)
		checksum = hashObject.hexdigest()
		
		#print postedOn + "	" + thePostItself + "	" + postedAt + "	" + checksum
		localList.append(postedOn)
		localList.append(thePostItself)
		localList.append(normalizedPostedAt)
		localList.append(checksum)
		self.rowOfDataInDb.append(localList)
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# test method to check if the rowOfDataInDb is populated properly or not
	def displayAllRows(self):
		print "\nThe prepared content is "
		for i in self.rowOfDataInDb :
			print i
		# displaying the list in sorted order if at all required in any case
		print "\nThe prepared content sorted chronologically is "
		chronologically = sorted(self.rowOfDataInDb, key=itemgetter(2))
		for i in chronologically:
			print i
	# ----------------------------------------------------------------------------------------------------------------------------------------
##############################################################################################################################################


##############################################################################################################################################
# This class has the logic to scrape Pastebin for a given search term 
class PastebinScrape(ScrapeHelper):

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method that initializes takes care of what part of the response page holds the timestamp of the post
	def __init__(self, helperObject):
		self.uniqueToken = "paste_box_line2"
		self.timeStampSection = "div.paste_box_line2 span"
		self.timeStampContainer = "title"
		self.searchedItem = helperObject.currentlySearchingFor

		if " " in helperObject.currentlySearchingFor:
			self.searchedItem = helperObject.currentlySearchingFor.replace(" ", "%20")

		self.mainUrl = 'https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=filtered_cse&num=10&hl=en&prettyPrint=false&source=gcsc&gss=.com&sig=56f70d816baa48bdfe9284ebc883ad41&cx=013305635491195529773:0ufpuq-fpt0&q=' + self.searchedItem +'&sort=&googlehost=www.google.com&callback=google.search.Search.apiary3563'
		helperObject.timeStampHolder[0] = self.uniqueToken
		helperObject.timeStampHolder[1] = self.timeStampSection
		helperObject.timeStampHolder[2] = self.timeStampContainer
		self.domain = "pastebin"
		self.actualPost = None
		self.postTime = None
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method that actually scrapes Pastebin
	def scrapeIt(self, helperObject):
		response = requests.get(self.mainUrl)
		#print response
		if (response.status_code == 200):
			#print response.text
			if(response.text.find('clicktrackUrl') >= 0):
				#print "\nResults FOUND!"
				counter = 0
				startIndex = response.text.find('(')
				endIndex = response.text.rfind(')')
				resString = response.text[startIndex + 1 : endIndex]
				#print "\n\nREsposne string is "
				#print resString
				unquoted = urllib.unquote(resString)
				jsonObjToParse = json.loads(unquoted)
				#print type(jsonObjToParse)
				#print "\n\n\n\n OK this is it "
				#print jsonObjToParse['results']
				total = len(jsonObjToParse['results'])
				#print "length is total " + str(total)
				while (counter < total):
					link = jsonObjToParse['results'][counter]['unescapedUrl']
					ts = helperObject.extractPostTime(link)
					# in case the post is deleted/removed from pastebin, the request still returns a 200 but the timestamp is no longer present on 
					# page and hence in that case, it returns None. So checking for such a case below and skipping it if found. 
					if(ts is None):
						print "\nPost has been removed !"
						counter = counter + 1
						continue
					# We directly have the link to the post in pastebin. So our actual post param hods just the link. 
					# Hitting this link in the browser would take you to the actual post itself.
					self.actualPost = str(link)
					self.postTime = str(ts)
					print "Url is " + self.actualPost + " and it was posted at " + self.postTime
					helperObject.prepareDbData(self.domain, self.actualPost, self.postTime)
					counter = counter + 1

			else:
				print "\nBooo...! the lad's missing !"
		else:
			print response.status_code
			print "\nNo response received\n\n"
	# ----------------------------------------------------------------------------------------------------------------------------------------
##############################################################################################################################################


##############################################################################################################################################
# This class has the logic to scrape Pastie and Google for a given search term
class PastieGoogleScrape(ScrapeHelper):

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method that initializes takes care of what part of the response page holds the timestamp of the post
	def __init__(self, helperObject):
		self.uniqueToken = "paste_date"
		self.timeStampSection = "span.typo_date"
		self.timeStampContainer = "title"
		self.searchedItem = helperObject.currentlySearchingFor
		
		if " " in helperObject.currentlySearchingFor:
			self.searchedItem = helperObject.currentlySearchingFor.replace(" ", "+")

		self.mainUrl = 'https://google.co.in/search?q=' + self.searchedItem +'+site:pastie.org'
		helperObject.timeStampHolder[0] = self.uniqueToken
		helperObject.timeStampHolder[1] = self.timeStampSection
		helperObject.timeStampHolder[2] = self.timeStampContainer
		self.domain = "pastieGoogle"
		self.actualPost = None
		self.postTime = None
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method that actually scrapes Pastie and Google
	def scrapeIt(self, helperObject):
		headers = {
					'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:40.0) Gecko/20100101 Firefox/40.0',
					'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
					'Connection': 'keep-alive'
				}
		response = requests.get(self.mainUrl, headers = headers)
		#print response
		if (response.status_code == 200):
			#print response.text
			if(response.text.find('<cite class="_Rm">') >= 0):
				#print "\nResults FOUND!"
				soup = BeautifulSoup(response.text, 'html.parser')

				if(soup):
					#print "\nHot Soup Ready "
					elms = soup.select("h3.r a")
					for i in elms:
						link = i.attrs["href"]
						ts = helperObject.extractPostTime(link)
						# We directly have the link to the post in pastie and Google. So our actual post param holds just the link. 
						# Hitting this link in the browser would take you to the actual post itself.
						self.actualPost = str(link)
						self.postTime = str(ts)
						print "Url is " + self.actualPost + " and it was posted at " + self.postTime
						helperObject.prepareDbData(self.domain, self.actualPost, self.postTime)
				else:
					print "\nCould not make the soup !!"

			else:
				print "\nBooo...! the lad's missing !"
		else:
			print response.status_code
			print "\nNo response received\n\n"
	# ----------------------------------------------------------------------------------------------------------------------------------------
##############################################################################################################################################


##############################################################################################################################################
# This class has the logic to scrape Google for a given search term
class GoogleScrape(ScrapeHelper):

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method that initializes takes care of what part of the response page holds the timestamp of the post
	def __init__(self, helperObject):
		self.uniqueToken = "paste_date"
		self.timeStampSection = "span.typo_date"
		self.timeStampContainer = "title"
		self.searchedItem = helperObject.currentlySearchingFor
		
		if " " in helperObject.currentlySearchingFor:
			self.searchedItem = helperObject.currentlySearchingFor.replace(" ", "+")

		self.mainUrl = 'https://google.co.in/search?q=' + self.searchedItem
		helperObject.timeStampHolder[0] = self.uniqueToken
		helperObject.timeStampHolder[1] = self.timeStampSection
		helperObject.timeStampHolder[2] = self.timeStampContainer
		self.domain = "Google"
		self.actualPost = None
		self.postTime = None
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method that actually scrapes Pastie and Google
	def scrapeIt(self, helperObject):
		headers = {
					'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:40.0) Gecko/20100101 Firefox/40.0',
					'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
					'Connection': 'keep-alive'
				}
		response = requests.get(self.mainUrl, headers = headers)
		#print response
		if (response.status_code == 200):
			#print response.text
			if(response.text.find('<cite class="_Rm">') >= 0):
				#print "\nResults FOUND!"
				soup = BeautifulSoup(response.text, 'html.parser')

				if(soup):
					#print "\nHot Soup Ready "
					elms = soup.select("h3.r a")
					for i in elms:
						link = i.attrs["href"]
						# In case of a Google link, we may not necessarily have a timestamp on the linked page. Hence keeping the ts = None here
						# Corresponding to None, null would be inserted in the DB. 
						ts = None
						# We directly have the link to the post in pastie and Google. So our actual post param holds just the link. 
						# Hitting this link in the browser would take you to the actual post itself.
						self.actualPost = str(link)
						self.postTime = str(ts)
						print "Url is " + self.actualPost + " and it was posted at " + self.postTime
						helperObject.prepareDbData(self.domain, self.actualPost, self.postTime)
				else:
					print "\nCould not make the soup !!"

			else:
				print "\nBooo...! the lad's missing !"
		else:
			print response.status_code
			print "\nNo response received\n\n"
	# ----------------------------------------------------------------------------------------------------------------------------------------
##############################################################################################################################################


##############################################################################################################################################
# This class has the logic to scrape Reddit for a given search term
class RedditScrape(ScrapeHelper):
	
	# ----------------------------------------------------------------------------------------------------------------------------------------
	# for reddit we are using the PRAW Python Module. To do a search a unique user agent is required. This is what (and if required other
	# things in the future) we are initializing here. 
	def __init__(self, helperObject):
		self.userAgent = 'goJek_social_monitor'
		self.domain = "reddit"
		self.actualPost = None
		self.postTime = None
		self.resultsFound = False
		self.client_id = helperObject.moreConfig['apiTokens']['reddit_client_id']
		self.client_secret = helperObject.moreConfig['apiTokens']['reddit_client_secret']
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method that actually scrapes Reddit
	def scrapeIt(self, helperObject):
		r = praw.Reddit(client_id = self.client_id, client_secret=self.client_secret, user_agent = self.userAgent)
		submissions = r.subreddit('all').search(helperObject.currentlySearchingFor, limit=10)
		for x in submissions:
			# We directly have the link to the post in Reddit. So our actual post param hods just the link. 
			# Hitting this link in the browser would take you to the actual post itself.
			self.resultsFound = True
			self.actualPost = str(x.shortlink)
			time = x.created
			ts = datetime.datetime.fromtimestamp(time)
			self.postTime = str(ts)
			message = str(x) + " & the link is " + self.actualPost + " at " + self.postTime
			print message
			helperObject.prepareDbData(self.domain, self.actualPost, self.postTime)
		
		if not self.resultsFound:
			print "\nBooo...! the lad's missing !"
	# ----------------------------------------------------------------------------------------------------------------------------------------
##############################################################################################################################################


##############################################################################################################################################
# This class has the logic to scrape Twitter for a given search term
class TwitterScrape(ScrapeHelper):

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# For twitter we are using the python module Twitter Search - which is a wrapper around the standard APIs provided by Twitter.
	# We need to initialize consumer key and secret and access token and secret. That's what (and other is required in the future) we are doing
	# here.
	def __init__(self, helperObject):
		# it's about time to create a TwitterSearch object with our secret tokens
		self.ts = TwitterSearch(
			consumer_key = helperObject.moreConfig['apiTokens']['twitter_consumer_key'],
			consumer_secret = helperObject.moreConfig['apiTokens']['twitter_consumer_secret'],
			access_token = helperObject.moreConfig['apiTokens']['twitter_access_token'],
			access_token_secret = helperObject.moreConfig['apiTokens']['twitter_access_token_secret']
		 )
		self.domain = "twitter"
		self.actualPost = None
		self.postTime = None
		self.resultsFound = False
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method that actually scrapes Twitter
	def scrapeIt(self, helperObject):
		try:
			tso = TwitterSearchOrder() # create a TwitterSearchOrder object
			tso.set_keywords([helperObject.currentlySearchingFor]) # let's define all words we would like to have a look for
			tso.set_include_entities(False) # and don't give us all those entity information
			
			for tweet in self.ts.search_tweets_iterable(tso):
				# We directly have the link to the Tweet itself. So our actual post param hods just the link. 
				# Hitting this link in the browser would take you to the actual tweet itself.
				self.resultsFound = True
				self.actualPost = "https://twitter.com/statuses/" + str(tweet['id'])
				self.postTime = str(tweet['created_at'].encode("utf-8"))
				print "@" + str((tweet['user']['screen_name']).encode("utf-8")) + " tweeted " + str(tweet['text'].encode("utf-8")) + "and the time was " + self.postTime + " and the id of the tweet is " + self.actualPost
				helperObject.prepareDbData(self.domain, self.actualPost, self.postTime)
			
			if not self.resultsFound:
				print "\nBooo...! the lad's missing !"
			
			print "\n\n"
		
		except TwitterSearchException as e: # take care of all those ugly errors if there are some
			print(e)
	# ----------------------------------------------------------------------------------------------------------------------------------------
##############################################################################################################################################


##############################################################################################################################################
# This class handles all the database interactions
class DataAccessObject(ScrapeHelper):
	
	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method to connect to the database and initialize the tables etc.
	def __init__(self, helperObject):
		#print "initializing db ..."
		filterwarnings('ignore', category = mdb.Warning)
		self.con = None
		self.cur = None
		self.dbName = helperObject.moreConfig['dbAccess']['db']
		self.dbUser = helperObject.moreConfig['dbAccess']['username']
		self.dbPass = helperObject.moreConfig['dbAccess']['password']
		createTableQry = "CREATE TABLE IF NOT EXISTS scraped_data(searched_for VARCHAR(100), searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, search_result VARCHAR(250), posted_at DATETIME, search_source VARCHAR(100), search_hash CHAR(40), PRIMARY KEY (search_hash))"

		try:
			self.con = mdb.connect('localhost', self.dbUser, self.dbPass, self.dbName)
			self.cur = self.con.cursor()
			self.cur.execute(createTableQry)
			self.con.commit()

		except mdb.Error, e:
			if self.con:
				self.con.rollback()
			print "Error %d: %s" % (e.args[0],e.args[1])
			if self.con:
				self.con.close()
			exit(1)

		# initializing the mailer 
		self.alerter = AlertMailer(helperObject)
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method to insert rows in the table
	def addNewResultsToDb(self, helperObject):
		insertValueQry = "INSERT INTO scraped_data (searched_for, search_source, search_result, posted_at, search_hash) VALUES (%s, %s, %s, %s, %s)"
		# In order to update the db with just the new pastes, we select the search_hash column from the db and populate it in a local list. Now for 
		# every new row to be inserted in the db, we first check if the hash of the new row to be inserted already exists in the local list. If so,
		# we do not insert the row in the db, else we do
		selectHashQry = "SELECT search_hash FROM scraped_data"
		existingHashesInDb = []
		insertValues = []
		insertValues.append(helperObject.currentlySearchingFor)
		insertValues.append(None)
		insertValues.append(None)
		insertValues.append(None)
		insertValues.append(None)
		try:
			self.cur.execute(selectHashQry)
			if (self.cur.rowcount):
				# print "that is the result set is not empty and at least one row was found"
				for searchHash in self.cur:
					existingHashesInDb.append(searchHash[0]) # because searchhash is a tuple

			for aScrapedRecord in helperObject.rowOfDataInDb :
				#print aScrapedRecord
				counter = 1
				for eachValue in aScrapedRecord:
					#print eachValue
					insertValues[counter] = eachValue
					counter = counter + 1

				if(insertValues[3] is not None):
					# Time conversion needed only when it is available. In case of Google link, it may not be available. So in that case it would just be None
					# so that null would be inserted in the db in the respective column
					mySqlDateTimeFormattedPostedAt = insertValues[3].strftime('%Y-%m-%d %H:%M:%S')

				else:
					mySqlDateTimeFormattedPostedAt = None

				#print "Mysql formatted datetime string is " + mySqlDateTimeFormattedPostedAt
				if(len(existingHashesInDb)):
					# for x in existingHashesInDb:
					# 	print x
					# print "that is there was hashes found earlier. So we will insert only if hash of current search does not exist in the db"
					if(insertValues[4] not in existingHashesInDb):
						print "NEW LAD IN TOWN... PULLING ONBOARD ! " #+ insertValues[4]
						self.cur.execute(insertValueQry,(insertValues[0], insertValues[1], insertValues[2], mySqlDateTimeFormattedPostedAt, insertValues[4]))
						self.con.commit()
						# now each time there is a new entry in the db, the existingHashesInDb needs to be updated
						existingHashesInDb.append(insertValues[4])
						self.alerter.sendAlertNow("Fresh Entry ! Checkout the DB for " + insertValues[4] + "\n" + insertValues[0] + " was found on " + insertValues[1] + " at "  + str(insertValues[3]) + " and you may check it out on " + insertValues[2])

				else:
					# that is there was no hashes found. This is the first run of the script. So just pump in all the results in the db
					print "Loading booties... !"
					self.cur.execute(insertValueQry,(insertValues[0], insertValues[1], insertValues[2], mySqlDateTimeFormattedPostedAt, insertValues[4]))
					self.con.commit()
					self.alerter.sendAlertNow("Fresh Entry ! Checkout the DB for " + insertValues[4] + "\n" + insertValues[0] + " was found on " + insertValues[1] + " at "  + str(insertValues[3]) + " and you may check it out on " + insertValues[2])

		except mdb.Error, e:
			if self.con:
				self.con.rollback()
			print "Error %d: %s" % (e.args[0],e.args[1])
			exit(1)

		finally:
			if self.con:
				self.con.close()
	# ----------------------------------------------------------------------------------------------------------------------------------------
##############################################################################################################################################


##############################################################################################################################################
# This class handles all the mailing functionality
class AlertMailer(ScrapeHelper):
	
	# ----------------------------------------------------------------------------------------------------------------------------------------
	# initializing the mailer. For mailer to function you may need to do some changes to your gmail settings itself. Checkout 
	# https://support.google.com/accounts/answer/6010255 while logged into your gmail account in the browser and follow the 
	# steps. 
	def __init__(self, helperObject):
		self.gmail_user = helperObject.moreConfig['mailerAccess']['username']
		self.gmail_pwd = helperObject.moreConfig['mailerAccess']['password']
		self.FROM = self.gmail_user
		self.recipient = helperObject.moreConfig['mailerAccess']['to']
		self.TO = self.recipient if type(self.recipient) is list else [self.recipient]
		self.SUBJECT = helperObject.moreConfig['mailerAccess']['subject']
		self.TEXT = "Note: This alert was sent by a Python and not a human !!\r\n\r\n"
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method that actually sends out the mails.
	def sendAlertNow(self, mailBody):
		# Prepare actual message
		message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
		""" % (self.FROM, ", ".join(self.TO), self.SUBJECT, self.TEXT + mailBody)
		
		try:
			server = smtplib.SMTP("smtp.gmail.com", 587)
			server.ehlo()
			server.starttls()
			server.login(self.gmail_user, self.gmail_pwd)
			server.sendmail(self.FROM, self.TO, message)
			server.close()
			print 'Alert !! Scoot over to your configured mail !'
		
		except:
			print "Tumsay na ho pawegaa bachhwaa !!\n"
			print "For mailer to function you may need to do some changes to your gmail settings itself. Checkout https://support.google.com/accounts/answer/6010255 while logged into your gmail account in the browser and follow the steps.\n SCRIPTING GODS BE WITH YOU !! "
	# ----------------------------------------------------------------------------------------------------------------------------------------
##############################################################################################################################################


##############################################################################################################################################
if __name__ == "__main__":

	helperObj = ScrapeHelper()
	# checking if there was just 1 searhc term specified, in which case we need not iterate over it, contrary to what we do in case we have a list 
	# of search terms. We simply assign that as the currentlySearchingFor. By default if the search_term has multiple comma separated values, search_term beocmes a list 
	# and each comma separated value a single item in the list
	if (type(helperObj.searchKeyWords) is not list ):
		print "\nla-la-la-ing for you !! :D "
		# converting the search term to a list, so that for searchTerm in helperObj.searchKeyWords: does not break. If not done, the search term becomes a 
		# a single string and hence when "searchTerm in helperObj.searchKeyWords:" this happens, search term basically starts picking each character from 
		# the string.
		tempList = []
		tempList.append(helperObj.searchKeyWords)
		helperObj.searchKeyWords = []
		helperObj.searchKeyWords.append(tempList[0])

	for searchTerm in helperObj.searchKeyWords:
		helperObj.currentlySearchingFor = searchTerm
		
		print "\n[+] Scrapping Pastebin for " + searchTerm + " ... "
		pastebinObj = PastebinScrape(helperObj)
		pastebinObj.scrapeIt(helperObj)

		print "\n[+] Scrapping Pastie for " + searchTerm + " ... "
		pastieGoogleObj = PastieGoogleScrape(helperObj)
		pastieGoogleObj.scrapeIt(helperObj)

		print "\n[+] Scrapping Google for " + searchTerm + " ... "
		googleObj = GoogleScrape(helperObj)
		googleObj.scrapeIt(helperObj)

		print "\n[+] Scrapping Reddit for " + searchTerm + " ... "
		redditObj = RedditScrape(helperObj)
		redditObj.scrapeIt(helperObj)

		print "\n[+] Scrapping Twitter for " + searchTerm + " ... "
		twitterObj = TwitterScrape(helperObj)
		twitterObj.scrapeIt(helperObj)

		#helperObj.displayAllRows() # uncomment if you need to see each of the records being pushed into the db

		print "\n[+] Talking to the storage ..."
		dao = DataAccessObject(helperObj)
		dao.addNewResultsToDb(helperObj)
		print "\n All aboard !"
##############################################################################################################################################
