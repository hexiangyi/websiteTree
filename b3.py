#coding=utf--8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from sc3 import Sitemapper
import pdb

t = Sitemapper()
#t.main('http://www.google.com')
#t.main('http://www.theonion.com')
#t.main('http://www.baidu.com')
linkInfos = None #t.main('http://www.huilanyujia.com')

import cPickle as p
dumpF = file('c:\\infos','wb')
p.dump(linkInfos,dumpF)



f = open('c:\\zTree\\html.html','w')
head = u'var zNodes = ['
tail = u'];'

encoding = 'utf-8'
f.write(head.encode(encoding))
for bean in linkInfos:
    pid = 0 if None == bean.parent else bean.parent.id
    bInfo = u'''{ id: %d, pId: %d, name:"%s", url: "%s",target:"_blank"},''' % (bean.id,pid,bean.title.strip().replace(u'\n',u''),bean.link)
    f.write(bInfo.encode(encoding,errors='ignore'))
f.write(tail.encode(encoding))
f.close()
print "--- Done~"    
pdb.set_trace()
pass
print u''
