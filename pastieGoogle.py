# pastie does not have a search API. Hitting it's search GET query directly actually is the same as doing a Google search for the keyword. 

import requests
from bs4 import BeautifulSoup

def extractPostTime(url, tsSection):
	response = requests.get(url)
	print response
	if (response.status_code == 200):
		#print response.text
		if(response.text.find(timeStampHolder[0])):
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
timeStampHolder.append("paste_date")
timeStampHolder.append("span.typo_date")
timeStampHolder.append("title")

headers = {
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Connection': 'keep-alive'
}

response = requests.get('https://google.co.in/search?q=ola+cabs+site:pastie.org&gws_rd=cr,ssl&ei=pfvvVerUA4aJuATquqXABA', headers = headers)
print response
if (response.status_code == 200):
	#print response.text
	if(response.text.find('<cite class="_Rm">') >= 0):
		print "\nResults FOUND!"
		soup = BeautifulSoup(response.text)

		if(soup):
			print "\nHot Soup Ready "
			#print soup

			# results = soup.findAll("h3", { "class" : "r" })
			# for content in results:
			# 	print content
			# 	#print type(content)
			# 	# soup = BeautifulSoup(content)
			# 	actResults = content.find_all('a', href=True)
			# 	print actResults[0]['href']
			elms = soup.select("h3.r a")
			for i in elms:
				#print(i.attrs["href"])
				link = i.attrs["href"]
				ts = extractPostTime(link, timeStampHolder)
				print "Url is " + str(link) + " and it was posted at " + str(ts)
		else:
			print "\nCould not make the soup !!"

	else:
		print "\n\nNOT DONE"
else:
	print response.status_code
	print "\nNo response received\n\n"


