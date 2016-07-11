from functools import wraps

from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map, Rule

from flask import current_app, request
from flask_socketio import join_room, leave_room

from .exc import InvalidRequestError, InvalidURIError, SocketAPIError


class SocketAPI(object):

    def __init__(self, socketio=None, namespace=None):
        self.namespace = namespace

        self.routes = Map()
        self.urls = self.routes.bind('/', '/')

        self.patch_handlers = {}

        if socketio is not None:
            self.init_socketio(socketio)

    def init_socketio(self, socketio):
        self.socketio = socketio

        @socketio.on('create', namespace=self.namespace)
        def handle_create(payload):
            # Retreive request arguments.
            if 'uri' not in payload:
                raise InvalidRequestError('missing URI')
            uri = payload['uri']
            attributes = payload.get('attributes', {})

            # Search for a matching route.
            try:
                creator, kwargs = self.urls.match(uri, method='POST')
            except HTTPException:
                # No registered resource creator for this uri.
                raise InvalidRequestError("no registered resource creator for %s'" % uri)

            # Create the new resource instance.
            kwargs.update(attributes)
            resource = creator(**kwargs)

            # Send the creation event to all subscribers of the uri.
            self.socketio.emit('create', {
                'uri': uri,
                'resource': resource
            }, room=uri)

        @socketio.on('patch')
        def handle_patch(payload, namespace=self.namespace):
            # Retreive request arguments.
            if 'uri' not in payload:
                raise InvalidRequestError('missing URI')
            uri = payload['uri']
            patch = payload.get('patch', {})

            # Search for a matching route.
            try:
                rule, kwargs = self.urls.match(uri, return_rule=True, method='PATCH')
                kwargs['patch'] = patch
            except HTTPException:
                # No registered resource patcher for this uri.
                raise InvalidRequestError("no registered resource patcher for %s'" % uri)

            # Call all the resource patchers for the given uri.
            for patch_handler in self.patch_handlers[rule.rule]:
                patch_handler(**kwargs)

            # Send the patch event to all subscribers of the resource, and of
            # the resource list.
            for room_name in (uri, uri[0:len(uri) - len(uri.split('/')[-1])]):
                self.socketio.emit('patch', {
                    'uri': uri,
                    'patch': patch
                }, room=room_name)

        @socketio.on('delete', namespace=self.namespace)
        def handle_delete(payload):
            # Retreive request arguments.
            if 'uri' not in payload:
                raise InvalidRequestError('missing URI')
            uri = payload['uri']

            # Search for a matching route.
            try:
                deleter, kwargs = self.urls.match(uri, method='DELETE')
            except HTTPException:
                # No registered resource deleter for this uri.
                raise InvalidRequestError("no registered resource deleter for %s'" % uri)

            # Delete the resource.
            resource = deleter(**kwargs)

            # Send the deletion event to all subscribers of the resource, and
            # of the resource list.
            for room_name in (uri, uri[0:len(uri) - len(uri.split('/')[-1])]):
                self.socketio.emit('delete', {
                    'uri': uri
                }, room=room_name)

        @socketio.on('subscribe', namespace=self.namespace)
        def handle_subscribe(uri):
            # Try to retrieve the subscribed resource, so that we can send its
            # current state to the subscriber.
            try:
                getter, kwargs = self.urls.match(uri, method='GET')
                resource = getter(**kwargs)
            except HTTPException:
                resource = None

            if resource is not None:
                self.socketio.emit('state', {
                    'uri': uri,
                    'resource': resource
                }, room=request.sid)

            join_room(uri)

        @socketio.on('unsubscribe', namespace=self.namespace)
        def handle_unsubscribe(uri):
            leave_room(uri)

        @socketio.on_error(self.namespace)
        def handle_error(e):
            if isinstance(e, SocketAPIError):
                # Instances of SocketAPIError are forwarded to the client.
                self.socketio.emit('api_error', {
                    'error':  e.__class__.__name__,
                    'message': str(e)
                }, room=request.sid)
            else:
                # Other errors are considered server errors and should not be
                # forwarded to the client, except in debug mode.
                self.socketio.emit('server_error', {
                    'error':  e.__class__.__name__,
                    'message': str(e) if current_app.debug else None
                }, room=request.sid)

            # Log the error.
            current_app.logger.exception(e)

    def resource_creator(self, rule):
        # Make sure the given rule corresponds to a list uri.
        if not rule.endswith('/'):
            raise InvalidURIError('resource creators should be registered on list uri')

        def decorate(fn):
            @wraps(fn)
            def decorated(*args, **kwargs):
                return fn(*args, **kwargs)

            # Register a new POST route for the given rule.
            self.routes.add(Rule(rule, endpoint=decorated, methods=['POST']))

            return decorated
        return decorate

    def resource_getter(self, rule):
        def decorate(fn):
            @wraps(fn)
            def decorated(*args, **kwargs):
                return fn(*args, **kwargs)

            # Register a new GET route for the given rule.
            self.routes.add(Rule(rule, endpoint=decorated, methods=['GET']))

            return decorated
        return decorate

    def resource_patcher(self, rule):
        # Make sure the rule doesn't correspond to a list.
        if rule.endswith('/'):
            raise InvalidURIError('cannot register resource patchers on a list uri')

        def decorate(fn):
            @wraps(fn)
            def decorated(*args, **kwargs):
                return fn(*args, **kwargs)

            # Check if there already is a route to catch patch requests on the
            # given rule.
            for route in self.routes.iter_rules():
                if (route.rule == rule) and ('PATCH' in route.methods):
                    break
            else:
                # Register a new PATCH route for the given rule.
                self.routes.add(Rule(rule, methods=['PATCH']))

            # Register the given patch handler.
            if rule not in self.patch_handlers:
                self.patch_handlers[rule] = []
            self.patch_handlers[rule].append(decorated)

            return decorated
        return decorate

    def resource_deleter(self, rule):
        # Make sure the rule doesn't correspond to a list.
        if rule.endswith('/'):
            raise InvalidURIError('cannot register resource deleters on a list uri')

        def decorate(fn):
            @wraps(fn)
            def decorated(*args, **kwargs):
                return fn(*args, **kwargs)

            # Register a new DELETE route for the given rule.
            self.routes.add(Rule(rule, endpoint=decorated, methods=['DELETE']))

            return decorated
        return decorate
