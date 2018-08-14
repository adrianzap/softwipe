"""
This module contains output classes, that is classes that are used to describe the output of a particular program in
a way that is easy to handle.
"""


class QmcalcOutput:
    """
    Contains the important parts of the qmcalc output. Important note: an object of this class is created by calling
    the constructor with the whole qmcalc output as one single parameter! The constructor will then parse the output
    and create all the variables.
    """
    def __init__(self, qmcalc_output):
        split_output = qmcalc_output.split()

        self.line_length_max = split_output[5]
        self.statement_nesting_mean = split_output[11]
        self.ngoto = split_output[18]
        self.nregister = split_output[21]
        self.style_inconsistency = split_output[41]
        self.cyclomatic_min = split_output[49]
        self.cyclomatic_max = split_output[52]
        self.cyclomatic_mean = split_output[50]

    def print_all_values(self):
        print('Maximum line length:', self.line_length_max)
        print('Average nesting of statements:', self.statement_nesting_mean)
        print('# goto statements:', self.ngoto)
        print('# register statements:', self.nregister)
        print('Style inconsistency:', self.style_inconsistency)
        print('Minimum cyclomatic complexity:', self.cyclomatic_min)
        print('Maximum cyclomatic complexity:', self.cyclomatic_max)
        print('Mean cyclomatic complexity:', self.cyclomatic_mean)


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
