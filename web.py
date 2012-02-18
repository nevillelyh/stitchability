import os
import random
import urlparse

import gevent.pywsgi

import stitchability

PORT = 80
STATIC_DIR = 'static'
CACHE_DIR = 'cache'
TEXT_HTML = ('Content-Type', 'text/html')

handlers = {}


def handle(uri):
    def wrapper(f):
        handlers[uri] = f
        return f
    return wrapper


def static_page(name):
    with open(os.path.join(STATIC_DIR, name), 'r') as f:
        return f.read().decode('utf-8')
    return u''


def link_page(url):
    up = urlparse.urlparse(url)
    domain = '%s://%s' % (up.scheme, up.netloc)
    html = [static_page('header.tmpl').format(title='Stitchability')]
    html.append(u'<form action="/" method="POST">')
    data = stitchability.get_data(url)
    for t, u in data['links']:
        if not t or not u or not u.startswith(domain):
            continue
        html.append(
            u'<input type="checkbox" name="url" value="{url}" checked="true"/>'
            .format(url=u))
        html.append(
            u'{text} - <a href="{url}">{surl}</a><br />'
            .format(text=t, url=u,
                surl=u[len(url):] if u.startswith(url) else u))
    html.append(u'<input type="hidden" name="title" value="{title}" />'
        .format(title=data['title']))
    html.append(u'<input type="submit" value="Submit" />')
    html.append(static_page('footer.tmpl'))
    return '\n'.join(html)


def randhash():
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(chars[random.randint(0, 61)] for i in xrange(8))


@handle('/')
def index(method, get=None, post=None):
    if method == 'GET':
        if 'url' not in get:
            return static_page('index.html')
        else:
            return link_page(get['url'][0])
    elif method == 'POST':
        html = [static_page('header.tmpl')
            .format(title=post['title'][0].decode('utf-8'))]
        html.append(stitchability.stitch(post['url']))
        html.append(static_page('footer.tmpl'))
        fhash = randhash()
        while os.path.exists(os.path.join(CACHE_DIR, fhash)):
            fhash = randhash()
        with open(os.path.join(CACHE_DIR, fhash), 'w') as f:
            f.write('\n'.join(html).encode('utf-8'))
            return static_page('redirect.tmpl').format(url=fhash)
    else:
        return ''


def application(env, start_response):
    uri = env['PATH_INFO']
    method = env['REQUEST_METHOD']
    get = urlparse.parse_qs(env.get('QUERY_STRING'), '')
    lines = env['wsgi.input'].readlines()
    post = urlparse.parse_qs(lines[0]) if lines else {}
    if uri in handlers:
        try:
            html = handlers[uri](method, get, post)
            start_response('200 OK', [TEXT_HTML])
            return [html.encode('utf-8')]
        except:
            raise
            start_response('500 Internal Error', [TEXT_HTML])
            return ['500 Internal Error']
    elif os.path.exists(os.path.join(CACHE_DIR, uri.lstrip('/'))):
        start_response('200 OK', [TEXT_HTML])
        with open(os.path.join(CACHE_DIR, uri.lstrip('/')), 'r') as f:
            return [f.read()]
    else:
        start_response('404 Not Found', [TEXT_HTML])
        return ['404 Not Found']

if __name__ == '__main__':
    gevent.pywsgi.WSGIServer(('', PORT), application).serve_forever()
