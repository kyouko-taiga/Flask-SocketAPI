import unittest
import coverage

cov = coverage.coverage()
cov.start()

from flask import Flask
from flask_socketio import SocketIO, rooms
from flask_socketapi import SocketAPI
from flask_socketapi.exc import InvalidURIError


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
socketapi = SocketAPI(socketio=socketio)


apples = {}


@socketapi.resource_creator('/apples/')
def create_apple(foo, bar=None):
    global apples
    key = max(apples.keys()) + 1 if apples else 0
    apples[key] = {
        'foo': foo,
        'bar': bar
    }
    return apples[key]


@socketapi.resource_getter('/apples/')
def list_apples():
    global apples
    return list(apples.values())


@socketapi.resource_getter('/apples/<int:key>')
def get_apples(key):
    global apples
    return apples[key]


@socketapi.resource_patcher('/apples/<int:key>')
def patch_apple_foo(key, patch):
    global apples
    apples[key]['foo'] = patch.get('foo', apples[key]['foo'])


@socketapi.resource_patcher('/apples/<int:key>')
def patch_apple_bar(key, patch):
    global apples
    apples[key]['bar'] = patch.get('bar', apples[key]['bar'])


@socketapi.resource_deleter('/apples/<int:key>')
def delete_apple(key):
    global apples
    del apples[key]


class TestSocketAPI(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        cov.stop()
        cov.report(include='flask_socketapi/socketapi.py')

    def test_subscription(self):
        client = socketio.test_client(app)
        client.emit('subscribe', '/oranges/0')

        self.assertIn('/oranges/0', socketio.server.rooms(client.sid))

    def test_unsubscription(self):
        client = socketio.test_client(app)
        client.emit('subscribe', '/oranges/0')
        client.emit('unsubscribe', '/oranges/0')

        self.assertNotIn('/oranges/0', socketio.server.rooms(client.sid))

    def test_list_subscription_with_getter(self):
        global apples
        apples[0] = {'foo': 0, 'bar': 'koala'}
        apples[1] = {'foo': 1, 'bar': 'camel'}

        client = socketio.test_client(app)
        client.emit('subscribe', '/apples/')
        received = client.get_received()

        self.assertIn('/apples/', socketio.server.rooms(client.sid))

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'state')
        self.assertIn({'foo': 0, 'bar': 'koala'}, received[0]['args'][0]['resource'])
        self.assertIn({'foo': 1, 'bar': 'camel'}, received[0]['args'][0]['resource'])

        apples.clear()

    def test_item_subscription_with_getter(self):
        global apples
        apples[0] = {'foo': 0, 'bar': 'koala'}
        apples[1] = {'foo': 1, 'bar': 'camel'}

        client = socketio.test_client(app)
        client.emit('subscribe', '/apples/0')
        received = client.get_received()

        self.assertIn('/apples/0', socketio.server.rooms(client.sid))

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'state')
        self.assertEqual({'foo': 0, 'bar': 'koala'}, received[0]['args'][0]['resource'])

        apples.clear()

    def test_create(self):
        global apples

        client = socketio.test_client(app)
        client.emit('create', {
            'uri': '/apples/',
            'attributes': {'foo': 0, 'bar': 'koala'}
        })

        self.assertEqual(len(apples), 1)
        self.assertIn({'foo': 0, 'bar': 'koala'}, apples.values())

        apples.clear()

    def test_patch(self):
        global apples
        apples[0] = {'foo': 0, 'bar': 'koala'}
        apples[1] = {'foo': 1, 'bar': 'camel'}

        client = socketio.test_client(app)
        client.emit('patch', {
            'uri': '/apples/0',
            'patch': {'foo': 2, 'bar': 'crane'}
        })

        self.assertEqual({'foo': 2, 'bar': 'crane'}, apples[0])
        self.assertEqual({'foo': 1, 'bar': 'camel'}, apples[1])

        apples.clear()

    def test_delete(self):
        global apples
        apples[0] = {'foo': 0, 'bar': 'koala'}
        apples[1] = {'foo': 1, 'bar': 'camel'}

        client = socketio.test_client(app)
        client.emit('delete', {
            'uri': '/apples/0'
        })

        self.assertEqual(len(apples), 1)
        self.assertNotIn({'foo': 0, 'bar': 'koala'}, apples.values())

        apples.clear()

    def test_list_subscription_events(self):
        global apples
        apples[0] = {'foo': 0, 'bar': 'koala'}
        apples[1] = {'foo': 1, 'bar': 'camel'}

        client = socketio.test_client(app)
        client.emit('subscribe', '/apples/')
        client.get_received()

        client.emit('create', {
            'uri': '/apples/',
            'attributes': {'foo': 2, 'bar': 'crane'}
        })
        received = client.get_received()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'create')
        self.assertEqual(received[0]['args'][0]['uri'], '/apples/')
        self.assertEqual({'foo': 2, 'bar': 'crane'}, received[0]['args'][0]['resource'])

        client.emit('patch', {
            'uri': '/apples/0',
            'patch': {'foo': 2, 'bar': 'crane'}
        })
        received = client.get_received()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'patch')
        self.assertEqual(received[0]['args'][0]['uri'], '/apples/0')
        self.assertEqual({'foo': 2, 'bar': 'crane'}, received[0]['args'][0]['patch'])

        client.emit('delete', {
            'uri': '/apples/0'
        })
        received = client.get_received()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'delete')
        self.assertEqual(received[0]['args'][0]['uri'], '/apples/0')

        apples.clear()

    def test_item_subscription_events(self):
        global apples
        apples[0] = {'foo': 0, 'bar': 'koala'}
        apples[1] = {'foo': 1, 'bar': 'camel'}

        client = socketio.test_client(app)
        client.emit('subscribe', '/apples/0')
        client.get_received()

        client.emit('patch', {
            'uri': '/apples/0',
            'patch': {'foo': 2, 'bar': 'crane'}
        })
        received = client.get_received()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'patch')
        self.assertEqual(received[0]['args'][0]['uri'], '/apples/0')
        self.assertEqual({'foo': 2, 'bar': 'crane'}, received[0]['args'][0]['patch'])

        client.emit('delete', {
            'uri': '/apples/0'
        })
        received = client.get_received()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]['name'], 'delete')
        self.assertEqual(received[0]['args'][0]['uri'], '/apples/0')

        apples.clear()

    def test_missing_resource_creator(self):
        client = socketio.test_client(app)
        client.emit('create', {
            'uri': '/oranges/',
            'attributes': {'foo': 2, 'bar': 'crane'}
        })
        received = client.get_received()

        self.assertEqual(received[0]['name'], 'api_error')
        self.assertEqual(received[0]['args'][0]['error'], 'InvalidRequestError')

    def test_missing_resource_patcher(self):
        client = socketio.test_client(app)
        client.emit('patch', {
            'uri': '/oranges/0',
            'patch': {'foo': 2, 'bar': 'crane'}
        })
        received = client.get_received()

        self.assertEqual(received[0]['name'], 'api_error')
        self.assertEqual(received[0]['args'][0]['error'], 'InvalidRequestError')

    def test_missing_resource_deleter(self):
        client = socketio.test_client(app)
        client.emit('delete', {
            'uri': '/oranges/0'
        })
        received = client.get_received()

        self.assertEqual(received[0]['name'], 'api_error')
        self.assertEqual(received[0]['args'][0]['error'], 'InvalidRequestError')

    def test_missing_request_uri(self):
        client = socketio.test_client(app)

        for method in ['create', 'patch', 'delete']:
            client.emit(method, {})
            received = client.get_received()

            self.assertEqual(received[0]['name'], 'api_error')
            self.assertEqual(received[0]['args'][0]['error'], 'InvalidRequestError')

    def test_server_error(self):
        client = socketio.test_client(app)
        client.emit('patch', {
            'uri': '/apples/0',
            'patch': {'foo': 2, 'bar': 'crane'}
        })
        received = client.get_received()

        self.assertEqual(received[0]['name'], 'server_error')
        self.assertEqual(received[0]['args'][0]['error'], 'KeyError')

    def test_invalid_resource_creator(self):
        try:
            @socketapi.resource_creator('/0')
            def invalid_resource_creator():
                pass
        except Exception as e:
            self.assertIsInstance(e, InvalidURIError)

    def test_invalid_resource_patcher(self):
        try:
            @socketapi.resource_patcher('/')
            def invalid_resource_patcher():
                pass
        except Exception as e:
            self.assertIsInstance(e, InvalidURIError)

    def test_invalid_resource_deleter(self):
        try:
            @socketapi.resource_deleter('/')
            def invalid_resource_deleter():
                pass
        except Exception as e:
            self.assertIsInstance(e, InvalidURIError)


if __name__ == '__main__':
    unittest.main()
