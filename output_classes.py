"""
This module contains output classes, that is classes that are used to describe the output of a particular program in
a way that is easy to handle.
"""


import strings
import classifications


class CppcheckOutput:
    """
    Contains a count for each type of warning that cppcheck has.
    Important note: the constructor takes as argument the warning_lines as obtained by the
    static_analysis_phase.get_cppcheck_warning_lines_from_cppcheck_output() function. From that list of lines,
    it extracts all information it needs.
    """
    def __init__(self, warning_lines):
        self.error_count = 0
        self.warning_count = 0
        self.style_count = 0
        self.portability_count = 0
        self.information_count = 0
        self.performance_count = 0
        self.total_weighted_count = 0

        for line in warning_lines:
            split_line = line.split()
            warning_type = [substring for substring in split_line if substring.startswith('(') and substring.endswith(
                ')')][0]

            # Add to the count of this warning type
            if warning_type == '(error)':
                self.error_count += 1
            elif warning_type == '(warning)':
                self.warning_count += 1
            elif warning_type == '(style)':
                self.style_count += 1
            elif warning_type == '(portability)':
                self.portability_count += 1
            elif warning_type == '(information)':
                self.information_count += 1
            elif warning_type == '(performance)':
                self.performance_count += 1

            # Add to the total weighted count
            warning_type_without_parentheses = warning_type[1:-1]
            warning_level = 1
            if warning_type_without_parentheses in classifications.CPPCHECK_WARNINGS:
                warning_level = classifications.CPPCHECK_WARNINGS[warning_type_without_parentheses]
            self.total_weighted_count += warning_level

    def print_information(self, lines_of_code):
        if self.error_count > 0:
            error_rate = self.error_count / lines_of_code
            print('Error rate:', strings.RATE_COUNT_TOTAL.format(error_rate, self.error_count, lines_of_code))
        if self.warning_count > 0:
            warning_rate = self.warning_count / lines_of_code
            print('Warning rate:', strings.RATE_COUNT_TOTAL.format(warning_rate, self.warning_count, lines_of_code))
        if self.style_count > 0:
            style_rate = self.style_count / lines_of_code
            print('Style warning rate:', strings.RATE_COUNT_TOTAL.format(style_rate, self.style_count, lines_of_code))
        if self.portability_count > 0:
            portability_rate = self.portability_count / lines_of_code
            print('Portability issue rate:', strings.RATE_COUNT_TOTAL.format(portability_rate, self.portability_count,
                                                                             lines_of_code))
        if self.performance_count > 0:
            performance_rate = self.performance_count / lines_of_code
            print('Performance issue rate:', strings.RATE_COUNT_TOTAL.format(performance_rate, self.performance_count,
                                                                             lines_of_code))
        # Information count is omitted because it is not considered interesting

        total_cppcheck_rate = self.total_weighted_count / lines_of_code
        print(strings.RESULT_WEIGHTED_CPPCHECK_WARNING_RATE.format(total_cppcheck_rate, self.total_weighted_count,
                                                                   lines_of_code))


class LizardOutput:
    """
    Contains the important information of the output of Lizard.

    Attributes:
        average_cyclomatic_complexity: The average cyclomatic complexity of all functions.
        warning_count: The number of Lizard warnings. These warnings indicate too high cyclomatic complexity,
        too long functions, or too many function parameters.
        duplicate_rate: The duplicate rate
        unique_rate: The unique rate
        function_count: The total number of functions
    """
    def __init__(self, average_cyclomatic_complexity, warning_count, duplicate_rate, unique_rate, function_count):
        self.average_cyclomatic_complexity = average_cyclomatic_complexity
        self.warning_count = warning_count
        self.duplicate_rate = duplicate_rate
        self.unique_rate = unique_rate
        self.function_count = function_count

    def print_information(self):
        print('Average cyclomatic complexity:', self.average_cyclomatic_complexity)
        warning_rate = self.warning_count / self.function_count
        print('Lizard warning rate (~= rate of functions that are too complex):', strings.RATE_COUNT_TOTAL.format(
            warning_rate, self.warning_count, self.function_count))
        print('Duplicate rate:', self.duplicate_rate)
        print('Unique rate:', self.unique_rate)
