from flask import Flask, render_template, json

from flask_socketio import SocketIO
from flask_socketapi import SocketAPI
from flask_socketapi.stores import SimpleStore

from todo import Todo, TodoEncoder


# Create the Flask application.
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.json_encoder = TodoEncoder

# Create the SocketIO object.
socketio = SocketIO(app, json=json)

# Create the SocketAPI object.
socketapi = SocketAPI(socketio=socketio, store=SimpleStore([(Todo, 'id')]))

# Register the subscribable resource.
socketapi.add_subscribable(Todo, 'id')


@socketapi.patch_handler(Todo)
def handle_patch_todo(object_, patch):
    for attribute, value in patch.items():
        setattr(object_, attribute, value)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, debug=True)
