import copy
import sys
from queue import PriorityQueue
from typing import Callable


class PrioritizedFunction:
    """
    Generic Prioritized function class.

    We need this class because there are no comparison operators defined on the function type.
    """

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

    This class can create filters and execute them on arguments. A filter is essentially a prioritized list of functions
    that work as a pipeline. The function pipeline gets its input arguments from do_filter and first executes the first
    function in the pipeline. The second function then gets as input the output of the first function and so on.

    Functions can be passed with a priority (e.g. 5). This means that any functions with a higher priority (e.g.
    """

    def __init__(self):
        """Initialize."""
        self._filters = PriorityQueue()

    def add_filter(self, callback: Callable, place: int = sys.maxsize):
        """
        Add a function to a filter with a specified name and place.

        :param callback: the function to add to the filter name
        :param place: the place in the order to add the function
        :return: None
        """
        self._filters.put((place, PrioritizedFunction(callback)))

    def _get_queue_as_list(self):
        """Get the queue reversed, as a list."""
        return_value = list()
        queue_copy = PriorityQueue()
        queue_copy.queue = copy.copy(self._filters.queue)
        while not queue_copy.empty():
            _, prioritized_function = queue_copy.get()
            return_value.append(prioritized_function.callback)
        return return_value

    def do_filter(self, *args):
        """
        Execute a filter by iteratively executing all its registered callbacks.

        :param args: the arguments to provide to the functions
        :return: filtered arguments
        """
        args_copy = copy.deepcopy(*args)
        for callback in self._get_queue_as_list():
            args_copy = callback(args_copy)
        return args_copy
