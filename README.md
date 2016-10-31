# Scrapper
Script to scrape from different social media platforms depending on the search word/s specified by the user in the config file. The results are stored in a MySql db as well. Currently the supported platforms are Pastebin, Pastie, 
Google, Reddit, Twitter. The results are obtained either through a direct search query on the platform or through 
a REST API exposed by the platform - NOT AN ELEGANT WAY OF DOING IT ! 

In a future release however, focus would be on <br>
1. consuming streaming APIs exposed by the various platforms.<br>
2. Multithreading the requests to various platforms<br>
3. Having a dashboard (may be measuring the social sentiments of posts on the various platforms) showing a more 
   statistical data if possible. <br>
4. And having a more efficient alerting mechanism than mails (if possible)<br>

<b>The main entry point to the script is khabri.py</b><br>
Ensure that the required python modules are installed and the required config.cfg is in place before running the script. 
The script may have some fancy debug messages --> that was to just kill the boring debug messages ! 

The config file has to be of the form : <br>
[display] # this section is not really implemented as of now. <br>
debug=false<br>
<br>
[keyword]<br>
search_term = comma separated search terms<br>
<br>
[dbAccess]<br>
db = dbName<br>
username = dbUser<br>
password = dbPassword<br>
<br>
[mailerAccess]<br>
username = gmail account from which you want to send mails<br>
password = password for the above (IMPORTANT - the config file should be stored securely)<br>
to = email id/(in case of ids it's a comma separated list)  where the alerts should be sent<br>
subject = Trust me over time these alerts (like anything else in this universe) would get boring. So you would want to have the subject as something that at least tickles you...atleast !<br>
<br>
[apiTokens] # holds the respective token for different services. For now since it's only twitter keys needed for twitter, it contains details about twitter alone.<br>
twitter_consumer_key = <br>
twitter_consumer_secret = <br>
twitter_access_token = <br>
twitter_access_token_secret = <br>
<br>
Save the file as config.cfg in the same dir as khabri.py<br>
