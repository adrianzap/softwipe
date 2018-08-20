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
    """
    def __init__(self, average_cyclomatic_complexity, warning_count):
        self.average_cyclomatic_complexity = average_cyclomatic_complexity
        self.warning_count = warning_count

    def print_information(self):
        print('Average cyclomatic complexity:', self.average_cyclomatic_complexity)
        print('Lizard warnings (~= number of functions that are too complex):', self.warning_count)


class CodeDuplicate:
    """
    Contains information about one detected piece of duplicate code as found by PMD CPD (Copy-Paste Detector).

    Attributes:
        lines: How many lines does the duplicate section span?
        tokens: How many tokens does the duplicate section include?
        occurrences: A list of tupels that describe the occurrences of the duplicate code. The tupel should look like
                     this: (file, line), where file is the file in which the duplicate occurs and line is the line at
                     which it starts. The whole list contains all such occurrences.
    """
    def __init__(self, lines, tokens, occurrences):
        self.lines = lines
        self.tokens = tokens
        self.occurrences = occurrences

    def print_information(self):
        print(str(self.lines), 'line and', str(self.tokens), 'tokens duplicate in:')
        for occurrence in self.occurrences:
            print('  ', occurrence[0], 'starting at line', occurrence[1])
