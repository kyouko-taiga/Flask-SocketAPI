from abc import ABCMeta, abstractmethod


class AbstractStore(metaclass=ABCMeta):
    """The Abstract Base Class for store interfaces.

    The SocketAPI object uses store interfaces to save and retreive the
    exposed resources, so that it can be agnostic of the backend used to
    actually manage them.
    """

    @abstractmethod
    def get(self, resource_class, id_attribute, resource_id):
        """Retrieves a resource from the store.

        :param resource_class:
            The class of the resource to retrieve.
        :param id_attribute:
            The name of the attribute to be used as the resource identifier.
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
