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
