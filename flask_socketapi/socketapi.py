from functools import wraps

from flask_socketio import join_room, leave_room

from .exc import InvalidRequestError, InvalidURIError, NotFoundError


class SocketAPI(object):

    def __init__(self, socketio=None, store=None, namespace=None):
        self.subscribable = {}
        self.store = store
        self.namespace = namespace

        if socketio is not None:
            self.init_socketio(socketio)

    def init_socketio(self, socketio):
        self.socketio = socketio

        @socketio.on('create', namespace=self.namespace)
        def handle_create(payload):
            # Retreive the resource class.
            if 'uri' not in payload:
                raise InvalidRequestError('missing URI')
            (resource_name, resource_id) = self._parse_uri(payload['uri'])
            resource_class = self.subscribable[resource_name]['class']

            if resource_id:
                raise InvalidURIError("'%s' is not a list" % payload['uri'])

            # Create the new resource instance.
            attributes = payload.get('attributes', {})
            resource = resource_class(**attributes)

            # Save the bew resource instance to the store.
            self.store.save(resource)

            # Send the creation event to all subscribers of the resource list.
            self.socketio.emit('create', {
                'uri': payload['uri'],
                'resource': resource
            }, room=payload['uri'])

        @socketio.on('patch')
        def handle_patch(payload, namespace=self.namespace):
            # Retreive the resource class.
            if 'uri' not in payload:
                raise InvalidRequestError('missing URI')
            (resource_name, resource_id) = self._parse_uri(payload['uri'])
            resource_class = self.subscribable[resource_name]['class']

            # Retreive the resource instance from the store.
            resource = self.store.get(resource_class, resource_id)
            if resource is None:
                raise NotFoundError(
                    'no %r resource identified by %r' % (resource_class.__name__, resource_id))

            # Call the resource patchers.
            patch = payload.get('patch', {})
            for patcher in self.subscribable[resource_name]['patchers']:
                patcher(resource, patch)

            # Save the resource instance to the store.
            self.store.save(resource)

            # Send the patch event to all subscribers of the resource, and the
            # resource list.
            for room_name in (resource_name + '/' + resource_id, resource_name + '/'):
                self.socketio.emit('patch', {
                    'uri': payload['uri'],
                    'patch': {attribute: getattr(resource, attribute) for attribute in patch}
                }, room=room_name)

        @socketio.on('delete', namespace=self.namespace)
        def handle_delete(payload):
            # Retreive the resource class.
            if 'uri' not in payload:
                raise InvalidRequestError('missing URI')
            (resource_name, resource_id) = self._parse_uri(payload['uri'])
            resource_class = self.subscribable[resource_name]['class']

            # Retreive the resource instance from the store.
            resource = self.store.get(resource_class, resource_id)
            if resource is None:
                raise NotFoundError(
                    'no %r resource identified by %r' % (resource_class.__name__, resource_id))

            # Delete the resource instance from the store.
            self.store.delete(resource)

            # Send the deletion event to all subscribers of the resource, and
            # the resource list.
            for room_name in (resource_name + '/' + resource_id, resource_name + '/'):
                self.socketio.emit('delete', {
                    'uri': payload['uri']
                }, room=room_name)

        @socketio.on('subscribe', namespace=self.namespace)
        def handle_subscribe(uri):
            (resource_name, resource_id) = self._parse_uri(uri)
            resource_class = self.subscribable[resource_name]['class']

            if resource_id:
                # Check that the resource we're trying to subscribe to exists.
                resource = self.store.get(resource_class, resource_id)
                if resource_id is None:
                    raise NotFoundError(
                        'no %r resource identified by %r' % (resource_class.__name__, resource_id))

                # Send a state event for the subscribed resource.
                self.socketio.emit('state', {
                    'uri': uri,
                    'resource': resource
                })
            else:
                resources = self.store.list(resource_class)
                self.socketio.emit('state', {
                    'uri': uri,
                    'resources': resources
                })

            join_room(uri)

        @socketio.on('unsubscribe', namespace=self.namespace)
        def handle_subscribe(uri):
            (resource_name, resource_id) = self._parse_uri(uri)
            leave_room(uri)

    def add_subscribable(self, resource_class, id_attribute):
        resource_name = resource_class.__name__.lower()
        self.subscribable[resource_name] = {
            'class': resource_class,
            'id_attribute': id_attribute,
            'patchers': []
        }

    def patch_handler(self, resource_class):
        resource_name = resource_class.__name__.lower()
        if resource_name not in self.subscribable:
            raise ValueError('undefined subscribable class %r' % resource_class.__name__)

        def decorate(fn):
            @wraps(fn)
            def decorated(*args, **kwargs):
                return fn(*args, **kwargs)

            self.subscribable[resource_name]['patchers'].append(decorated)

            return decorated
        return decorate

    def _parse_uri(self, uri):
        try:
            # If the uri identifies a single resource, it will have the form
            # `resource_name/resource_id`. If it identifies a resource list, it
            # have the form `resource_name/`. In the former case, `resource_id`
            # will be filled with the resource identifier, while in the latter it
            # will get the empty string.
            (resource_name, resource_id) = uri.split('/')
        except ValueError:
            # The given uri is necessary invalid if `str.split` raises an error.
            raise InvalidURIError

        resource_name = resource_name.lower()
        if resource_name not in self.subscribable:
            raise InvalidURIError

        return (resource_name, resource_id)
