import copy
from queue import PriorityQueue
from typing import Callable


class PrioritizedFunction:
    """Generic Prioritized function class."""

    def __init__(self, callback: Callable):
        """Initialize."""
        self.callback = callback

    def __str__(self) -> str:
        """Convert this object to string."""
        return self.callback.__name__

    def __lt__(self, obj):
        """Less than."""
        return str(self) < str(obj)

    def __le__(self, obj):
        """Less than or equal."""
        return str(self) <= str(obj)

    def __eq__(self, obj):
        """Equal."""
        return str(self) == str(obj)

    def __ne__(self, obj):
        """Not equal."""
        return str(self) != str(obj)

    def __gt__(self, obj):
        """Greater."""
        return str(self) > str(obj)

    def __ge__(self, obj):
        """Greater or equal."""
        return str(self) >= str(obj)


class Filter:
    """
    Generic Filter class.

    This class can create filters and execute them on arguments.
    """

    def __init__(self):
        """Initialize."""
        self.filters = PriorityQueue()

    def add_filter(self, callback: Callable, place: int = 1):
        """
        Add a function to a filter with a specified name and place.

        :param callback: the function to add to the filter name
        :param place: the place in the order to add the function
        :return: None
        """
        self.filters.put((-place, PrioritizedFunction(callback)))

    def do_filter(self, *args):
        """
        Execute a filter by iteratively executing all its registered callbacks.

        :param args: the arguments to provide to the functions
        :return: filtered arguments
        """
        queue_copy = PriorityQueue()
        queue_copy.queue = copy.copy(self.filters.queue)
        args_copy = copy.deepcopy(*args)
        while not queue_copy.empty():
            _, prioritized_function = queue_copy.get()
            args_copy = prioritized_function.callback(args_copy)
        return args_copy
