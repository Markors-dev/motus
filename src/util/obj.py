

class SingletonDecorator:
    """Creates a singleton class

    All decorated classed are stored in class attribute 'singleton_decorators'.
    """

    singleton_decorators = []

    def __init__(self, cls):
        SingletonDecorator.singleton_decorators.append(self)
        self.cls = cls
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance is None:
            self.instance = self.cls(*args, **kwargs)
        return self.instance

    @staticmethod
    def clean_instances():
        """Removes references to every singleton class

        This is needed so that the App can be restarted
        """
        for singletons in SingletonDecorator.singleton_decorators:
            singletons.instance = None


class AttrObject:
    """Empty class used as a container object for dinamic
    attribute assignment. """
