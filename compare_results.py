#!/usr/bin/env python3
"""
Compare all result rates and output the best and worst, or all rates sorted.
Parses the rates from files containing the output of softwipe for each program that should later be included in the
code quality benchmark, and sorts them.
"""

import argparse
import operator

from calculate_score_table import FOLDERS, SOFTWIPE_OUTPUT_FILE_NAME


def parse_arguments():
    parser = argparse.ArgumentParser(description='Compare all result rates and output the best and worst, '
                                                 'or all rates sorted.')
    parser.add_argument('result_directory', nargs=1, help='the directory where all result folders are saved in. For '
                                                          'each program that should later be included in the '
                                                          'code quality benchmark, a folder should exist in this '
                                                          'directory that contains the output of softwipe in a file '
                                                          'called "' + SOFTWIPE_OUTPUT_FILE_NAME + '"')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('-a', '--all', action='store_true', help='output all result rates, for each category, '
                                                               'in a sorted manner')
    mode.add_argument('-b', '--best', action='store_true', help='output only the best, second best, second worst, '
                                                                'and worst rates for each category')
    mode.add_argument('-B', '--best-only', action='store_true', help='output only the best and worst rates for each '
                                                                     'category')
    mode.add_argument('-s', '--softwipe', action='store_true', help='output suggested best & worst values for the '
                                                                    'scoring in softwipe, using the variable names '
                                                                    'softwipe uses such that the output can be copied '
                                                                    'into scoring.py easily. This is the default '
                                                                    'option')

    parser.add_argument('-n', '--no-average', action='store_true', help='do not print the average rate for any score')
    parser.add_argument('-m', '--no-median', action='store_true', help='do not print the median rate for any score')

    args = parser.parse_args()
    return args


def get_all_rates(result_directory):
    # TODO: file was not touched after test_count was added to benchmark -> check if everything is fine with this file

    # Init
    rates = {
        'compiler_and_sanitizer': [],
        'assertions': [],
        'cppcheck': [],
        'clang_tidy': [],
        'cyclomatic_complexity': [],
        'lizard_warnings': [],
        'unique': [],
        'kwstyle': [],
        'infer': [],
        'test_count': []
    }

    # Get all the rates
    for folder in FOLDERS:
        compiler_and_sanitizer_rate, assertion_rate, cppcheck_rate, clang_tidy_rate, ccn, lizard_rate, unique_rate, \
            kwstyle_rate, infer_rate, test_count_rate, \
            failed_tools = calculate_score_table.get_result_rates(result_directory, folder)

        rates['compiler_and_sanitizer'].append((folder, compiler_and_sanitizer_rate))
        rates['assertions'].append((folder, assertion_rate))
        rates['cppcheck'].append((folder, cppcheck_rate))
        rates['clang_tidy'].append((folder, clang_tidy_rate))
        rates['cyclomatic_complexity'].append((folder, ccn))
        rates['lizard_warnings'].append((folder, lizard_rate))
        rates['unique'].append((folder, unique_rate))
        rates['kwstyle'].append((folder, kwstyle_rate))
        rates['infer'].append((folder, infer_rate))
        rates['test_count'].append((folder, test_count_rate))

    return rates


def sort_rates(rates):
    """
    Return the rates dict such that every rate is sorted from best to worst.
    """
    sorted_rates = {}

    for rate in rates.keys():
        reverse = True if rate in ('assertions', 'unique') else False  # For these two rates, higher is better,
        # so sort in reverse order. For all other rates, lower is better.
        sorted_rates[rate] = sorted(rates[rate], key=operator.itemgetter(1), reverse=reverse)

    return sorted_rates


def calculate_median(list):
    if len(list) % 2 == 0:  # even number of elements
        median_higher_index = int(len(list) / 2)
        median_lower_index = median_higher_index - 1
        median = (list[median_lower_index][1] + list[median_higher_index][1]) / 2
    else:  # odd number of elements
        median_index = int(len(list) / 2)
        median = list[median_index][1]
    return median


def print_average_and_median(list_of_rates, no_average=False, no_median=False):
    if not no_average:
        average = sum(val[1] for val in list_of_rates) / len(list_of_rates)
        print('\t', 'Average:', average)

    if not no_median:
        median = calculate_median(list_of_rates)
        print('\t', 'Median:', median)

    if not (no_average and no_median):
        print()


def get_turkeys_fences(list):
    median = calculate_median(list)
    low_half_of_list = [val for val in list if val[1] <= median]
    high_half_of_list = [val for val in list if val[1] >= median]

    q1 = calculate_median(low_half_of_list)
    q3 = calculate_median(high_half_of_list)
    iqr = q3 - q1

    k = 1.5

    low_fence = q1 - k * iqr
    high_fence = q3 + k * iqr

    return low_fence, high_fence


def print_all_rates(sorted_rates, no_average=False, no_median=False):
    for rate in sorted_rates.keys():
        cur_list = sorted_rates[rate]
        low_fence, high_fence = get_turkeys_fences(cur_list)

        print(rate + ':', '(from best to worst)')
        for val in cur_list:
            outlier_string = ''
            if val[1] < low_fence:
                outlier_string = 'LOW OUTLIER'
            elif val[1] > high_fence:
                outlier_string = 'HIGH OUTLIER'

            print('\t', val[1], val[0], outlier_string)
        print()
        print_average_and_median(cur_list, no_average, no_median)


def print_softwipe_scoring_values(sorted_rates):
    for rate in sorted_rates.keys():
        cur_list = sorted_rates[rate]
        low_fence, high_fence = get_turkeys_fences(cur_list)

        i = 0
        while cur_list[i][1] < low_fence or cur_list[i][1] > high_fence:  # while the best value is an outlier
            i += 1
        best = cur_list[i][1]

        j = -1
        while cur_list[j][1] < low_fence or cur_list[j][1] > high_fence:  # while the worst value is an outlier
            j -= 1
        worst = cur_list[j][1]

        # Ugly string assignment code ahead :(
        best_string = ''
        worst_string = ''
        if rate == 'compiler_and_sanitizer':
            best_string = 'COMPILER_BEST'
            worst_string = 'COMPILER_WORST'
        elif rate == 'assertions':
            best_string = 'ASSERTIONS_BEST'
            worst_string = 'ASSERTIONS_WORST'
        elif rate == 'cppcheck':
            best_string = 'CPPCHECK_BEST'
            worst_string = 'CPPCHECK_WORST'
        elif rate == 'clang_tidy':
            best_string = 'CLANG_TIDY_BEST'
            worst_string = 'CLANG_TIDY_WORST'
        elif rate == 'cyclomatic_complexity':
            best_string = 'CYCLOMATIC_COMPLEXITY_BEST'
            worst_string = 'CYCLOMATIC_COMPLEXITY_WORST'
        elif rate == 'lizard_warnings':
            best_string = 'LIZARD_WARNINGS_BEST'
            worst_string = 'LIZARD_WARNINGS_WORST'
        elif rate == 'unique':
            best_string = 'UNIQUE_BEST'
            worst_string = 'UNIQUE_WORST'
        elif rate == 'kwstyle':
            best_string = 'KWSTYLE_BEST'
            worst_string = 'KWSTYLE_WORST'
        elif rate == 'infer':
            best_string = 'INFER_BEST'
            worst_string = 'INFER_WORST'
        elif rate == 'test_count':
            best_string = 'TEST_COUNT_BEST'
            worst_string = 'TEST_COUNT_WORST'

        print(best_string + ' = ' + str(best))
        print(worst_string + ' = ' + str(worst))
        print()


def print_best_rates(sorted_rates, no_average=False, no_median=False, only=False):
    for rate in sorted_rates.keys():
        cur_list = sorted_rates[rate]
        print(rate + ':')
        print('\t', 'Best:', cur_list[0][1], cur_list[0][0])
        if not only:
            print('\t', '2nd best:', cur_list[1][1], cur_list[1][0])
            print('\t', '2nd worst:', cur_list[-2][1], cur_list[-2][0])
        print('\t', 'Worst:', cur_list[-1][1], cur_list[-1][0])
        print()
        print_average_and_median(cur_list, no_average, no_median)


def print_best_rates_only(sorted_rates, no_average=False, no_median=False):
    print_best_rates(sorted_rates, no_average, no_median, only=True)


def main():
    args = parse_arguments()
    result_directory = args.result_directory[0]

    rates = get_all_rates(result_directory)
    sorted_rates = sort_rates(rates)

    if args.all:
        print_all_rates(sorted_rates, args.no_average, args.no_median)
    elif args.best:
        print_best_rates(sorted_rates, args.no_average, args.no_median)
    elif args.best_only:
        print_best_rates_only(sorted_rates, args.no_average, args.no_median)
    else:
        print_softwipe_scoring_values(sorted_rates)


if __name__ == "__main__":
    main()
