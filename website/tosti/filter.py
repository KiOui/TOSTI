import copy
from typing import Callable


class Filter:
    """
    Generic Filter class.

    This class can create filters and execute them on arguments.
    """

    def __init__(self):
        """Initialize."""
        self.filters = {}

    def add_filter(self, filter_name: str, callback: Callable, place: int = 0):
        """
        Add a function to a filter with a specified name and place.

        :param filter_name: the filter name to add the callback to
        :param callback: the function to add to the filter name
        :param place: the place in the order to add the function
        :return: None
        """
        if filter_name in self.filters.keys():
            self.filters[filter_name].insert(place, callback)
        else:
            self.filters[filter_name] = [callback]

    def do_filter(self, filter_name: str, *args):
        """
        Execute a filter by iteratively executing all its registered callbacks.

        :param filter_name: the filter name to execute
        :param args: the arguments to provide to the functions
        :return: filtered arguments
        """
        if filter_name in self.filters.keys():
            args_copy = copy.deepcopy(*args)
            for filter_callback in self.filters[filter_name]:
                args_copy = filter_callback(args_copy)
            return args_copy
        else:
            return args


# The default filter to use
function_filter = Filter()
