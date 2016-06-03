# coding: utf-8

import json
import logging
import requests
from deptest import depend_on
from mock_helper import mock_app, _url


app = mock_app()


def log_resp(resp):
    logging.info('resp, %s, %s', resp.status_code, resp.content)


logging.basicConfig(level=logging.INFO)


def test_post_posts():
    data = {
        'name': 'hello'
    }
    resp = requests.post(_url('/posts'), data=json.dumps(data))
    log_resp(resp)

    assert resp.status_code == 200
    assert 'id' in resp.json()

    return resp.json()


@depend_on('test_post_posts', with_return=True)
def test_get_posts(p):
    resp = requests.get(_url('/posts'))
    log_resp(resp)

    assert resp.status_code == 200
    d = resp.json()
    assert len(d) == len(app.db)
    assert d[0]['id'] == p['id']
    # assert 0


@depend_on('test_post_posts', with_return=True)
def test_get_post(p):
    resp = requests.get(_url('/posts/{}'.format(p['id'])))
    log_resp(resp)

    assert resp.status_code == 200
    d = resp.json()
    assert d['name'] == p['name']

    return p


@depend_on('test_get_post', with_return=True)
def test_put_post(p):
    new_p = dict(p)
    new_p['name'] = 'world'
    resp = requests.put(
        _url('/posts/{}'.format(p['id'])),
        data=json.dumps(new_p))
    log_resp(resp)

    assert resp.status_code == 200
    d = resp.json()
    assert d['name'] == new_p['name']


@depend_on('test_put_post')
@depend_on('test_get_post', with_return=True)
def test_delete_post(p):
    resp = requests.delete(_url('/posts/{}'.format(p['id'])))
    log_resp(resp)

    assert resp.status_code == 204
    assert len(app.db) == 0
    # assert 0
