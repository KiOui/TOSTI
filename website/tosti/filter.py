import copy
from typing import Callable


class Filter:
    """
    Generic Filter class.

    This class can create filters and execute them on arguments.
    """

    def __init__(self):
        """Initialize."""
        self.filters = []

    def add_filter(self, callback: Callable, place: int = 0):
        """
        Add a function to a filter with a specified name and place.

        :param callback: the function to add to the filter name
        :param place: the place in the order to add the function
        :return: None
        """
        self.filters.insert(place, callback)

    def do_filter(self, *args):
        """
        Execute a filter by iteratively executing all its registered callbacks.

        :param args: the arguments to provide to the functions
        :return: filtered arguments
        """
        args_copy = copy.deepcopy(*args)
        for filter_callback in self.filters:
            args_copy = filter_callback(args_copy)
        return args_copy
