from flask import Flask, render_template, json

from flask_socketio import SocketIO
from flask_socketapi import SocketAPI

from todo import Todo, TodoEncoder


# Create the Flask application.
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.json_encoder = TodoEncoder

# Create the SocketIO object.
socketio = SocketIO(app, json=json)

# Create the SocketAPI object.
socketapi = SocketAPI(socketio=socketio)

# Create a in-memory store for the todo items.
todos = {}


@socketapi.resource_creator('/todo/')
def create_todo(**kwargs):
    global todos
    todo = Todo(**kwargs)
    todos[todo.id] = todo
    return todo


@socketapi.resource_getter('/todo/')
def get_todo_list():
    global todos
    return list(todos.values())


@socketapi.resource_getter('/todo/<id_>')
def get_todo(id_):
    global todos
    return todos.get(id_)


@socketapi.resource_patcher('/todo/<id_>')
def patch_todo(id_, patch):
    global todos
    for attribute, value in patch.items():
        setattr(todos[id_], attribute, value)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, debug=True)
