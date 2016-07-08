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
from flask_socketapi import SocketAPI, AbstractStore

class Store(AbstractStore):

    def __init__(self, database):
        self.database = database

    def get(self, resource_class, id_attribute, resource_id):
        return self.database[resource_class.__name__][resource_id]

    def save(self, resource):
        self.database[resource.__class__.__name__][resource.identifier] = resource

    def delete(self, resource):
        del self.database[resource.__class__.__name__][resource.identifier]

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

DATABASE = {
    'Foo': {}
}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.json_encoder = FooEncoder
socketio = SocketIO(app)

socketapi = SocketAPI(socketio=socketio, store=Store(DATABASE))
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