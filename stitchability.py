import urllib2
import urlparse

import gevent
import readability
import lxml.html

def get_data(url):
    tree = lxml.html.parse(url)
    title = tree.find('head').find('title').text
    links = lxml.html.iterlinks(tree.find('body'))
    return {
        'title' : title,
        'links' : [(l[0].text, urlparse.urljoin(url, l[2])) for l in links],
        }

def stitch(urls):
    pool = [gevent.spawn(extract, url) for url in urls]
    gevent.joinall(pool)
    return '\n'.join([g.value for g in pool])

def extract(url):
    html = readability.Document(urllib2.urlopen(url).read()).summary()
    html = lstrip(html, '<html>')
    html = lstrip(html, '<body/>')
    html = rstrip(html, '</html>')
    return html.strip()

def lstrip(s, p):
    return s[len(p):] if s.startswith(p) else s

def rstrip(s, p):
    return s[:-len(p)] if s.endswith(p) else s