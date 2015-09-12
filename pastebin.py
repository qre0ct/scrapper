# playing with pastebin search. No API support. Direct search query and parsing the http response. 
# the main logic is to send a GET request to 
# http://pastebin.com/search?cx=013305635491195529773%3A0ufpuq-fpt0&cof=FORID%3A10&ie=UTF-8&q=olastore&sa.x=0&sa.y=0&sa=Search
# where in q would hold the user entered search key. 
# Now there is a catch here. When something is searched for in the pastebin searchbox, the results that you see are from Google search results.
# These are populated by pastebin through javascript. So when you initially fire the above search GET query, the response that you get is just 
# the bare response which contains the javascript to load the actual search results from Google. So if you simply parse the above response, you
# will not get any of the results that you see on the browser, becasue they are fetched later once the page loads and the js actually gets executed.
# So this js actually makes a hit to Google APIs with the API key for Pastebin that can be observed through Burp. The request that gets fired by the
# js is https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=filtered_cse&num=10&hl=en&prettyPrint=false&source=gcsc&gss=.com&sig=56f70d816baa48bdfe9284ebc883ad41&cx=013305635491195529773:0ufpuq-fpt0&q=olacabs&sort=&googlehost=www.google.com&callback=google.search.Search.apiary3563'
# And the response to this request actually holds all the search results. Hence we need to parse this repsone now to pick up all our results. 
# The reposnse to the above request is of the form of a javascript fucntion (named google.search.Search.apiary3563()) call which has all the search results 
# and other details (in the form of a json object) as the function argument. So we take this argument out and parse it as json object. For each returned result
# there is a key (named unescapedUrl) in the 'results' key, which is what we would parse out from there. 

import requests
import json
import urllib
from bs4 import BeautifulSoup

def extractPostTime(url, tsSection):
	response = requests.get(url)
	print response
	if (response.status_code == 200):
		#print response.text
		if(response.text.find(tsSection[0])):
			print "\nTime Stamp Found !"
			soup = BeautifulSoup(response.text)

			if(soup):
				print "\nHot Soup Ready "
				elms = soup.select(tsSection[1])
				for i in elms:
					return str(i.attrs[tsSection[2]])
			else:
				print "\nCould not make the soup !!"

		else:
			print "\n\nTime Stamp Not Found "
	else:
		print response.status_code
		print "\nNo response received\n\n"

timeStampHolder = []
timeStampHolder.append("paste_box_line2")
timeStampHolder.append("div.paste_box_line2 span")
timeStampHolder.append("title")

response = requests.get('https://www.googleapis.com/customsearch/v1element?key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=filtered_cse&num=10&hl=en&prettyPrint=false&source=gcsc&gss=.com&sig=56f70d816baa48bdfe9284ebc883ad41&cx=013305635491195529773:0ufpuq-fpt0&q=olacabs&sort=&googlehost=www.google.com&callback=google.search.Search.apiary3563')
print response
if (response.status_code == 200):
	print response.text
	if(response.text.find('clicktrackUrl') >= 0):
		print "\nResults FOUND!"
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
			ts = extractPostTime(link, timeStampHolder)
			print "Url is " + str(link) + " and it was posted at " + str(ts)
			counter = counter + 1

	else:
		print "\n\nNOT DONE"
else:
	print response.status_code
	print "\nNo response received\n\n"
