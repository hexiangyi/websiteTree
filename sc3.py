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
import LinkInfo
from LinkInfo import LinkInfo
import socket  #if lib does't support timeout arg, socket.setdefaulttimeout(30)
import traceback
import pdb
COUNT = 1
mutex = threading.Lock()

class Sitemapper():

	def assignID(self,linkInfo):
	   global COUNT, mutex
	   linkInfo.setID(COUNT)
	   #print "id is ",COUNT
	   COUNT += 1

	def main(self, start_url, block_extensions=['.pdf','.gif','.jpg','.JPG','.PNG','.png','.wav','.mp3','.wma'], max_urls = 100):

		# Set user agent string
		opener = urllib2.build_opener()
		opener.addheaders = [
			('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.220 Safari/535.1'),
			('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
			('Accept-Charset', 'utf-8,gbk;q=0.7,*;q=0.3'),
			#('Accept-Encoding', 'gzip,deflate,sdch'),
			('Accept-Language', 'en-US,en,en-zh;q=0.8'),
			#('Cache-Control', 'max-age=0'),
			#('Connection', 'keep-alive')
		]
		urllib2.install_opener(opener)

		# Get base info
		(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(start_url)
		fragments = (scheme, netloc, '', '', '', '')
		base_url = urlparse.urlunparse(fragments)
		#print "base_url  -> ", base_url
		
		mainLink = LinkInfo(None,base_url,u'Main',0,u'first page')
		self.assignID(mainLink)
		

		urls_queue = set([mainLink])
		urls_crawled = set()
		urls_crawled2 = set()

		pool = eventlet.GreenPool(20)

		counter = 0
		tmpC = 0
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
				urls_crawled2 = urls_crawled2.union(set([url]))

				# Extract links
				links = self.extract_links(url, body, block_extensions)
				if ( links == None ):return urls_crawled
				if tmpC == 100000 : return urls_crawled
				tmpC += 1
				for link in links:
					if link not in urls_queue and link not in urls_crawled:
						# Add link to queue
						urls_queue = urls_queue.union(set([link]))
						print u"[valid]: link -> ", link.link

		return urls_crawled

	def fetch(self, url):
		print u"opening", url.link

		try:
		        fails = 0
		        while True:
			    if fails >=2:return url,False
		            try:
			        page = urllib2.urlopen(url.link,timeout=30)
			    except:
			        print u'time out 30, retry ..',url.link
			        fails += 1
			        continue
			    break

			#DO NOT USE str because it can just handle ascii code
			'''When using Unicode, four points
			   1.string in the application should be used preffixed with u
			   2.Do NOT use str but unicode()
			   3.Do not use deprecated method string, it would strewthings up.  Ah~~~ 
			   4.do not encode and decode characters in your application untill you really need to do such as when you are writing a file to the disk, database, or network. use encode  and decode
			'''
			body = page.read()
			#print chardet.detect(body)
			result = chardet.detect(body)
			try:
			   #body = body.decode(result['encoding'])
			   body = unicode(body,result['encoding'],'ignore')
			except:
			   print u"decode err url:%s; body: %s" % (url.link,body)
			   pdb.set_trace()
			   traceback.print_exc()
			finally:
			   #print "decode err url:%s; body: %s" % (url,body)
			   pass
			
			#print u"body type ", type(body)
			return url, body#, charset
		except (urllib2.URLError, urllib2.HTTPError, Exception), detail:
			# Skip this node
			print u"ERROR %s" % detail
			print u"current wrong decoded url is %s" % url.link
			return url, False#, False

	def extract_links(self, url, body, block_extensions):
		print u" -- resolbing ", url.link  #, u" with type(body) -> ", type(body)
		'''(base_scheme, base_netloc, base_path, base_params, base_query, base_fragment) = urlparse.urlparse(url.link)
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
				#partial_link_url = str(link['href'].decode('gbk').encode)
				partial_link_url = link['href']
				#if( link['href'].find('www.huilanyujia.com') > 5):continue
			except KeyError:
				continue

			# Concatenate relative urls like "../joing.html" with currently being processed url
			link_url = urlparse.urljoin(url.link, partial_link_url)

			# Strip off any trailing jibberish like ?test=1
			(scheme, netloc, path, params, query, fragment) = urlparse.urlparse(link_url)
			fragments = (scheme, netloc, path, '', '', '')
			link_url = urlparse.urlunparse(fragments)

			# Make sure we're still on the same domain
			(base_scheme, base_netloc, base_path, base_params, base_query, base_fragment) = urlparse.urlparse(url.link)

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
			elif len(link.text) <= 0:
				# ignore url without title
				pass
			else:
				# Add this link to the list
				#print u"find link %s,  [%s]" % (link_url,link.text)
				#print u"find link", link_url , u"in url:",url.link
				#print u" link and txt type : ",type(link), type(link.text)
				try:
				    #print link.text
				    pass
				except:
				    print "text err ",link," ;in ",url.link," ,",type(link.text)
				    r = chardet.detect(body)
				    pdb.set_trace()
				    traceback_print_exc()
				#good_links.append(link_url)
				#pdb.set_trace()

				newLink = LinkInfo(url,link_url,link.text,0)
				self.assignID(newLink)
				#if url.parent == None:
				#   print u"pid = -1",u" id = ",newLink.id
				#else:
				#   print u"pid = ",newLink.parent.id,u" id = ",newLink.id


				good_links.append(newLink)

		return good_links
