# coding: utf-8

import requests
from deptest import depend_on


sessionid = '12345'


def test_set_cookie():
    s = requests.Session()

    resp = s.get('http://httpbin.org/cookies/set?sessionid={}'.format(sessionid),
                 allow_redirects=False)

    print resp.status_code, resp.content, resp.headers
    assert resp.status_code == 302
    assert 'Set-Cookie' in resp.headers

    return s


@depend_on('test_set_cookie', with_return=True)
def test_get_cookie(s):
    resp = s.get('http://httpbin.org/cookies')

    print resp.status_code, resp.content, resp.headers
    assert resp.status_code == 200
    assert resp.json()['cookies']['sessionid'] == sessionid
