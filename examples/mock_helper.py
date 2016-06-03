# coding: utf-8

"""
Use httpretty to simulate a simple restful service.
"""

import re
import json
import httpretty


class MockApp(object):
    def __init__(self, base_url):
        self.base_url = base_url
        httpretty.enable()
        httpretty.HTTPretty.allow_net_connect = False

    def route(self, method, uri):
        url = self.base_url + uri
        pattern = re.compile('{}$'.format(url))

        def deco(f):
            def request_handler(request, uri, headers):
                print 'got request', request, uri, headers
                matched = pattern.search(uri).groups()
                return f(request, *matched)

            httpretty.register_uri(
                getattr(httpretty, method),
                pattern,
                body=request_handler,
                streaming=True,
            )
            return f
        return deco


base_url = 'http://example.com'

_url = lambda x: base_url + x


def mock_app():
    app = MockApp(base_url)
    app.db = {}

    @app.route('GET', '/posts')
    def get_posts(req):
        return (200, {}, json.dumps(app.db.values()))

    @app.route('POST', '/posts')
    def post_posts(req):
        id = str(len(app.db.keys()) + 1)
        post = json.loads(req.body)
        post['id'] = id
        app.db[id] = post
        return (200, {}, json.dumps(post))

    @app.route('GET', '/posts/(\d+)')
    def get_post(req, id):
        p = app.db.get(id)
        if p:
            return (200, {}, json.dumps(p))
        else:
            return (404, {}, '')

    @app.route('PUT', '/posts/(\d+)')
    def put_post(req, id):
        p = app.db.get(id)
        if p:
            app.db[id] = json.loads(req.body)
            return (200, {}, json.dumps(app.db[id]))
        else:
            return (404, {}, '')

    @app.route('DELETE', '/posts/(\d+)')
    def delete_post(req, id):
        p = app.db.get(id)
        if p:
            del app.db[id]
            return (204, {}, '')
        else:
            return (404, {}, '')

    return app
