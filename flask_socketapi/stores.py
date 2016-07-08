from abc import ABCMeta, abstractmethod


class AbstractStore(metaclass=ABCMeta):
    """The Abstract Base Class for store interfaces.

    The SocketAPI object uses store interfaces to save and retreive the
    exposed resources, so that it can be agnostic of the backend used to
    actually manage them.
    """

    @abstractmethod
    def list(self, resource_class):
        """Retrieves a list of resources from the store.

        :param resource_class:
            The class of the resources to retrieve.

        :return:
            A list of instances of `resource_class`.
        """

    @abstractmethod
    def get(self, resource_class, resource_id):
        """Retrieves a resource from the store.

        :param resource_class:
            The class of the resource to retrieve.
        :param resource_id:
            The resource identifier.

        :return:
            An instance of `resource_class` or `None` if the resource couldn't
            be found.
        """

    @abstractmethod
    def save(self, resource):
        """Saves a resource to the store.

        :param resource:
            The resource to be saved.
        """

    @abstractmethod
    def delete(self, resource):
        """Deletes a resource from the store.

        :param resource:
            The resource to be deleted.
        """


class SimpleStore(AbstractStore):
    """A store implementation that keeps its resources in memory.

    This class exists mainly for development and is not thread safe.
    """

    def __init__(self, id_attributes):
        self._id_attributes = {
            name.__name__: id_attribute for (name, id_attribute) in id_attributes}
        self._database = {}

    def list(self, resource_class):
        try:
            return list(self._database[resource_class.__name__].values())
        except KeyError:
            return []

    def get(self, resource_class, resource_id):
        try:
            return self._database[resource_class.__name__][resource_id]
        except KeyError:
            return None

    def save(self, resource):
        try:
            resource_database = self._database[resource.__class__.__name__]
        except KeyError:
            self._database[resource.__class__.__name__] = {}
            resource_database = self._database[resource.__class__.__name__]

        id_attribute = self._id_attributes[resource.__class__.__name__]
        resource_database[getattr(resource, id_attribute)] = resource

    def delete(self, resource):
        try:
            id_attribute = self._id_attributes[resource.__class__.__name__]
            del self._database[resource.__class__.__name__][getattr(resource, id_attribute)]
        except KeyError:
            pass
