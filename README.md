# scrapper
Script to scrape from different social media platforms depending on the search word/s specified by the user in the config file. The results are stored in a MySql db as well. Currently the supported platforms are Pastebin, Pastie, 
Google, Reddit, Twitter. The results are obtained either through a direct search query on the platform or through 
a REST API exposed by the platform - NOT AN ELEGANT WAY OF DOING IT ! 

In a future release however, focus would be on 
1. consuming streaming APIs exposed by the various platforms.
2. Multithreading the requests to various platforms
3. Having a dashboard (may be measuring the social sentiments of posts on the various platforms) showing a more 
   statistical data if possible. 
4. And having a more efficient alerting mechanism than mails (if possible)

The main entry point to the script is khabri.py
Ensure that the required python modules are installed and the required config.cfg is in place before running the script. 
The script may have some fancy debug messages --> that was to just kill the boring debug messages ! 

