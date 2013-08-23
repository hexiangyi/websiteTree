"""
    AUTHOR: Darren Nix
    Version: 0.1
    Date:    2011-9-7
    Site: www.darrennix.com
    License: Apache 2.0

    Crawls a site to find unique page URLs and returns them as a list.
    Ignores query strings, badly formed URLs, and links to domains
    outside of the starting domain.
    
    Inspired by sitemap_gen from Valdimir Toncar


    DEPENDENCIES:
    BeautifulSoup HTML parsing library
    Eventlet

"""
import urlparse
from bs4 import BeautifulSoup
import cchardet as chardet
import eventlet
from eventlet.green import urllib2
import threading
count = 0
con = threading.Condition()

class Sitemapper():

	def main(self, start_url, block_extensions=['.pdf','.gif','.jpg','.JPG','.PNG','.png','.wav','.mp3','.wma'], max_urls = 100):

		# Set user agent string
		'''opener = urllib2.build_opener()
		opener.addheaders = [
			('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.220 Safari/535.1'),
			('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
			('Accept-Charset', 'utf-8,gbk;q=0.7,*;q=0.3'),
			('Accept-Encoding', 'gzip,deflate,sdch'),
			('Accept-Language', 'en-US,en,en-zh;q=0.8'),
			('Cache-Control', 'max-age=0'),
			('Connection', 'keep-alive')
		]
		urllib2.install_opener(opener)'''

		# Get base info
		(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(start_url)
		fragments = (scheme, netloc, '', '', '', '')
		base_url = urlparse.urlunparse(fragments)
		#print "base_url  -> ", base_url

		urls_queue = set([base_url])
		global count
		print u"id = ", count,u" name= u",base_url, u" pid = " , 0
		count +=1
		urls_crawled = set()

		pool = eventlet.GreenPool(20)

		counter = 0
		while True:
			#Infinite loop sanity check
			counter +=1
			if counter > max_urls:
				break

			for url, body in pool.imap(self.fetch, urls_queue):
				# Remove this url from the queue set
				urls_queue = urls_queue - set([url])

				# Add url to crawled set
				urls_crawled = urls_crawled.union(set([url]))

				# Extract links
				links = self.extract_links(url, body, block_extensions)
				if ( links == None ):return urls_crawled
				for link in links:
					if link not in urls_queue and link not in urls_crawled:
						# Add link to queue
						urls_queue = urls_queue.union(set([link]))
						print u"[valid]: link -> ", link

		return urls_crawled

	def fetch(self, url):
		print u"opening", url

		try:
			#body = urllib2.urlopen(url).read()  #.decode('utf-8')
			page = urllib2.urlopen(url)
			#global charset
			#charset = page.headers['Content-Type'].split('Charset=')[1].lower()
			#print "read url ", url
			#print "magic starts"
			#DO NOT USE str because it can just handle ascii code
			'''When using Unicode, four points
			   1.string in the application should be used preffixed with u
			   2.Do NOT use str but unicode()
			   3.Do not use deprecated method string, it would strewthings up.  Ah~~~ 
			   4.do not encode and decode characters in your application untill you really need to do such as when you are writing a file to the disk, database, or network. use encode  and decode
			'''
			body = page.read()
			print chardet.detect(body)
			result = chardet.detect(body)
			try:
			   body = body.decode(result['encoding'])
			except:
			   traceback.print_exc()
			   print "decode err url:%s; body: %s" % (url,body)
			finally:
			   #print "decode err url:%s; body: %s" % (url,body)
			   pass
			
			print u"body type ", type(body)
			#if( )
			#print "body len -> ", len(body)
			#print "type(body) ->", type(body)
			#print "body  -> ", body.decode('gbk')
			#print "body  -> ", body.decode('utf-8')
			#print "body  -> ", body.encode('UTF-8')
			return url, body#, charset
		except (urllib2.URLError, urllib2.HTTPError), detail:
			# Skip this node
			print u"ERROR %s" % detail
			print u"current wrong decoded url is %s" % url
			return url, False#, False

	def extract_links(self, url, body, block_extensions):
		# Soup it and find links
		#print " the link ", link, " is ", charset
		print u" -- resolbing ", url, u" with type(body) -> ", type(body)
		'''(base_scheme, base_netloc, base_path, base_params, base_query, base_fragment) = urlparse.urlparse(url)
		for blocked_extension in block_extensions:
		    if(base_path.find(blocked_extension) > 0):
		        print u" ----- hit---"
		        return
		'''
		if( isinstance(body,(unicode)) == False ): return []
		soup = BeautifulSoup(u''.join(body))
		#test code here
		#print BeautifulSoup(''.join(body)).get_text()
		#print BeautifulSoup((body),from_encoding="utf-8").get_text()
		
		links = soup.findAll('a')
		if (links == None):return []

		good_links = []
		# Loop through all the links on the page
		for link in links:

			# Ignore A tags without HREFs
			try:
				#print "partial_link_url - > ",link['href']
				#print "partial_link_url str - > ",str(link['href'],encoding='gbk')
				#partial_link_url = str(link['href'].decode('gbk').encode)
				partial_link_url = link['href']
				#if( link['href'].find('www.huilanyujia.com') > 5):continue
			except KeyError:
				continue

			# Concatenate relative urls like "../joing.html" with currently being processed url
			link_url = urlparse.urljoin(url, partial_link_url)

			# Strip off any trailing jibberish like ?test=1
			(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(link_url)
			fragments = (scheme, netloc, path, '', '', '')
			link_url = urlparse.urlunparse(fragments)

			# Make sure we're still on the same domain
			(base_scheme, base_netloc, base_path, base_params, base_query, base_fragment) = urlparse.urlparse(url)

			# Skip some file types
			blocked = False
			for blocked_extension in block_extensions:
				extension_length = len(blocked_extension)
				url_extension = path[-extension_length:]
				if url_extension == blocked_extension:
					blocked = True

			if netloc != base_netloc:
				# Different domain
				pass
			elif blocked:
				# bad extension
				pass
			else:
				# Add this link to the list
				#print u"find link %s,  [%s]" % (link_url,link.text)
				print u"find link", link_url 
				print u" link and txt type : ",type(link), type(link.text)
				print link.text
				print u"pid = ",url,u" id ="
				good_links.append(link_url)

		return good_links
