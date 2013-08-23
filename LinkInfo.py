class LinkInfo:
	def __init__(self,parent=None,link=u'#',title='',weight=0,description='',id=-1):
	    self.parent = parent
	    self.link = link
	    self.title = title
	    self.weight = weight
	    self.description = description
	    self.id = id

	def __cmp__(self,other):
	    if self.link > other.link:return 1
	    elif self.link == other.link:return 0
	    elif self.link < other.link:return -1

	def __eq__(self,other):
	    if type(self) == type(other) and self.link == other.link:return True
	    else:
	        return False
	def __hash__(self):
	    #return hash(self.link + u" " + self.title)
	    return hash(self.link + u" ")
	
	def setID(self,id=-1):
	    self.id =  id;


	'''def __setattr__(self,attr,value):
	     if attr == 'link' or attr == 'title' or attr == 'weight' or attr == 'description':
	        self.__dict__[attr] = value
	     else:
		      print attr," set err"
		      raise AttributeError,attr + ' not allowed'

	def __getattr__(self,attrname):
	     if attranme == 'link':return self.link
	     elif attrname == 'title':return self.title
	     elif attrname == 'weight':return self.weight
	     elif attrname == 'description':return self.description
	'''

