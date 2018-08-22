"""
This module contains output classes, that is classes that are used to describe the output of a particular program in
a way that is easy to handle.
"""


class LizardOutput:
    """
    Contains the important information of the output of Lizard.

    Attributes:
        average_cyclomatic_complexity: The average cyclomatic complexity of all functions.
        warning_count: The number of Lizard warnings. These warnings indicate too high cyclomatic complexity,
        too long functions, or too many function parameters.
        duplicate_rate: The duplicate rate
        unique_rate: The unique rate
    """
    def __init__(self, average_cyclomatic_complexity, warning_count, duplicate_rate, unique_rate):
        self.average_cyclomatic_complexity = average_cyclomatic_complexity
        self.warning_count = warning_count
        self.duplicate_rate = duplicate_rate
        self.unique_rate = unique_rate

    def print_information(self):
        print('Average cyclomatic complexity:', self.average_cyclomatic_complexity)
        print('Lizard warnings (~= number of functions that are too complex):', self.warning_count)
        print('Duplicate rate:', self.duplicate_rate)
        print('Unique rate:', self.unique_rate)
