import urllib2
import urlparse

import gevent
import readability
import lxml.html


def get_data(url):
    tree = lxml.html.parse(url)
    title = tree.find('head').find('title').text
    uniq = set()
    links = []
    for l in lxml.html.iterlinks(tree.find('body')):
        u = urlparse.urljoin(url, urlparse.urldefrag(l[2])[0])
        if u in uniq:
            continue
        links.append((l[0].text, u))
        uniq.add(u)
    return {
        'title': title,
        'links': links,
        }


def stitch(urls):
    pool = [gevent.spawn(extract, url) for url in urls]
    gevent.joinall(pool)
    return '<div>%s</div>' % ('\n'.join([g.value for g in pool]))


def extract(url):
    doc = readability.Document(urllib2.urlopen(url).read())
    title = doc.title()
    html = doc.summary()
    html = lstrip(html, '<html>')
    html = lstrip(html, '<body/>')
    html = rstrip(html, '</html>')
    return '<h1>%s</h1>%s' % (title, html.strip())


def lstrip(s, p):
    return s[len(p):] if s.startswith(p) else s


def rstrip(s, p):
    return s[:-len(p)] if s.endswith(p) else s
