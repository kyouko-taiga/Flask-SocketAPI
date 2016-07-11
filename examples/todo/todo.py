from flask import Flask, render_template
from flask.json import JSONEncoder


class Todo(object):

    def __init__(self, bar=None, text='', completed=False):
        self.id = str(id(self))
        self.text = text
        self.completed = completed


class TodoEncoder(JSONEncoder):

    def default(self, object_):
        if isinstance(object_, Todo):
            return object_.__dict__
        else:
            return JSONEncoder.default(self, object_)
