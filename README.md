Flask-SocketAPI
===============

Lightweight library to create streaming API over Flask-SocketIO.

Installation
------------

You can download and unzip the latest version of this package from github: [https://github.com/kyouko-taiga/Flask-SocketAPI/archive/master.zip](https://github.com/kyouko-taiga/Flask-SocketAPI/archive/master.zip).

Alternatively, if you have git installed on your system, you may prefer cloning the repository directly:

	git clone https://github.com/kyouko-taiga/Flask-SocketAPI.git

Then, simply navigate to the root directory of the package and run:

	python setup.py install

Example
-------

```python
from flask import Flask, render_template, json

from flask_socketio import SocketIO
from flask_socketapi import SocketAPI
from flask_socketapi.stores import SimpleStore


class Foo(object):

    def __init__(self, bar=None):
        self.identifier = id(self)
        self.bar = bar

class FooEncoder(json.JSONEncoder):

    def default(self, object_):
        if isinstance(object_, Foo):
            return object_.__dict__
        else:
            return json.JSONEncoder.default(self, object_)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.json_encoder = FooEncoder
socketio = SocketIO(app, json=json)

socketapi = SocketAPI(
	socketio=socketio, store=SimpleStore([(Foo, 'identifier')]))

socketapi.add_subscribable(Foo, 'identifier')

@socketapi.patch_handler(Foo)
def handle_patch_todo(object_, patch):
    for attribute, value in patch.items():
        setattr(object_, attribute, value)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app)
```