# Making the final integrated code that would call the scrappers for the different platforms. Trying to keep each it as modular as possible 
# to allow extensibility in terms of addition of more platforms later. 

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
import time
##############################################################################################################################################

##############################################################################################################################################
# The class that holds the common methods required for scrapping. 
class ScrapeHelper():
	
	# ----------------------------------------------------------------------------------------------------------------------------------------
	def __init__(self):
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
				soup = BeautifulSoup(response.text)

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

		# normalize the post time to a common format
		datetimeObj = parser.parse(postedAt)
		normalizedPostedAt = datetimeObj.replace(tzinfo=self.utc)

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
		self.mainUrl = 'https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=filtered_cse&num=10&hl=en&prettyPrint=false&source=gcsc&gss=.com&sig=56f70d816baa48bdfe9284ebc883ad41&cx=013305635491195529773:0ufpuq-fpt0&q=olacabs&sort=&googlehost=www.google.com&callback=google.search.Search.apiary3563'
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
				print "\n\nNOT DONE"
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
		self.mainUrl = 'https://google.co.in/search?q=ola+cabs+site:pastie.org&gws_rd=cr,ssl&ei=pfvvVerUA4aJuATquqXABA'
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
				soup = BeautifulSoup(response.text)

				if(soup):
					#print "\nHot Soup Ready "
					elms = soup.select("h3.r a")
					for i in elms:
						link = i.attrs["href"]
						ts = helperObject.extractPostTime(link)
						# We directly have the link to the post in pastie and Google. So our actual post param hods just the link. 
						# Hitting this link in the browser would take you to the actual post itself.
						self.actualPost = str(link)
						self.postTime = str(ts)
						print "Url is " + self.actualPost + " and it was posted at " + self.postTime
						helperObject.prepareDbData(self.domain, self.actualPost, self.postTime)
				else:
					print "\nCould not make the soup !!"

			else:
				print "\n\nNOT DONE"
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
		self.userAgent = 'olaCabs_social_monitor'
		self.domain = "reddit"
		self.actualPost = None
		self.postTime = None
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method that actually scrapes Reddit
	def scrapeIt(self, helperObject):
		r = praw.Reddit(user_agent = self.userAgent)
		submissions = r.search("ola cabs", limit=10)
		for x in submissions:
			# We directly have the link to the post in Reddit. So our actual post param hods just the link. 
			# Hitting this link in the browser would take you to the actual post itself.
			self.actualPost = str(x.short_link)
			time = x.created
			ts = datetime.datetime.fromtimestamp(time)
			self.postTime = str(ts)
			message = str(x) + " & the link is " + self.actualPost + " at " + self.postTime
			print message
			helperObject.prepareDbData(self.domain, self.actualPost, self.postTime)
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
			consumer_key = 'RLXY0g7xiLLs0zbU21QQd1neH',
			consumer_secret = 'c8NgW92oYjyOZfyNwRQjXSkasF0Cv3wGIO4dsjl2RyOCYZ3HzT',
			access_token = '3433982414-6p8ccwItkWO2GF90YiUIS30o6U3Fy10T50TouRB',
			access_token_secret = 'ZDY7QbfBZ1uvLjzjlF7A4zZxMSNgmoJo6qsbuuhlPAAPM'
		 )
		self.domain = "twitter"
		self.actualPost = None
		self.postTime = None
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method that actually scrapes Twitter
	def scrapeIt(self, helperObject):
		try:
			tso = TwitterSearchOrder() # create a TwitterSearchOrder object
			tso.set_keywords(['deepdevops']) # let's define all words we would like to have a look for
			tso.set_include_entities(False) # and don't give us all those entity information
			
			for tweet in self.ts.search_tweets_iterable(tso):
				# We directly have the link to the Tweet itself. So our actual post param hods just the link. 
				# Hitting this link in the browser would take you to the actual tweet itself.
				self.actualPost = "https://twitter.com/statuses/" + str(tweet['id'])
				self.postTime = str(tweet['created_at'].encode("utf-8"))
				print "@" + str((tweet['user']['screen_name']).encode("utf-8")) + " tweeted " + str(tweet['text'].encode("utf-8")) + "and the time was " + self.postTime + " and the id of the tweet is " + self.actualPost
				helperObject.prepareDbData(self.domain, self.actualPost, self.postTime)
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
		print "initializing db ..."
		self.con = None
		self.cur = None
		self.dbName = 'scrapperDb'
		self.dbUser = 'scrapperScript'
		self.dbPass = '5cr4p3r'
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
	# ----------------------------------------------------------------------------------------------------------------------------------------

	# ----------------------------------------------------------------------------------------------------------------------------------------
	# method to insert rows in the table
	def addNewResultsToDb(self, helperObject):
		insertValueQry = "INSERT INTO scraped_data (searched_for, search_source, search_result, posted_at, search_hash) VALUES (%s, %s, %s, %s, %s)"
		insertValues = []
		insertValues.append("Ola")
		insertValues.append(None)
		insertValues.append(None)
		insertValues.append(None)
		insertValues.append(None)
		try:
			for aScrapedRecord in helperObject.rowOfDataInDb :
				print aScrapedRecord
				counter = 1
				for eachValue in aScrapedRecord:
					print eachValue
					insertValues[counter] = eachValue
					counter = counter + 1
					
				mySqlDateTimeFormattedPostedAt = insertValues[3].strftime('%Y-%m-%d %H:%M:%S')
				print "Mysql formatted datetime string is " + mySqlDateTimeFormattedPostedAt

				self.cur.execute(insertValueQry,(insertValues[0], insertValues[1], insertValues[2], mySqlDateTimeFormattedPostedAt, insertValues[4]))
				self.con.commit()

		except mdb.Error, e:
			if self.con:
				self.con.rollback()
			print "Error %d: %s" % (e.args[0],e.args[1])
			exit(1)

		finally:
			if self.con:
				self.con.close()

##############################################################################################################################################


##############################################################################################################################################
if __name__ == "__main__":

	print "\n Scrapping Pastebin ... "
	helperObj = ScrapeHelper()
	pastebinObj = PastebinScrape(helperObj)
	pastebinObj.scrapeIt(helperObj)

	print "\n Scrapping Pastie and Google ... "
	pastieGoogleObj = PastieGoogleScrape(helperObj)
	pastieGoogleObj.scrapeIt(helperObj)

	print "\n Scrapping Reddit ... "
	redditObj = RedditScrape(helperObj)
	redditObj.scrapeIt(helperObj)

	print "\n Scrapping Twitter ... "
	twitterObj = TwitterScrape(helperObj)
	twitterObj.scrapeIt(helperObj)

	helperObj.displayAllRows()

	print "\n Talking to the storage ..."
	dao = DataAccessObject(helperObj)
	dao.addNewResultsToDb(helperObj)
##############################################################################################################################################
