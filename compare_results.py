#!/usr/bin/env python3
"""
Compare all result rates and output the best and worst, or all rates sorted.
Parses the rates from files containing the output of softwipe for each program that should later be included in the
code quality benchmark, and sorts them.
"""

import argparse
import operator
from calculate_score_table import SOFTWIPE_OUTPUT_FILE_NAME
from calculate_score_table import FOLDERS
import calculate_score_table


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
                                                                'and worst rates for each category. This is the '
                                                                'default option')
    mode.add_argument('-B', '--best-only', action='store_true', help='output only the best and worst rates for each '
                                                                     'category')

    parser.add_argument('-n', '--no-average', action='store_true', help='do not print the average rate for any score')
    parser.add_argument('-m', '--no-median', action='store_true', help='do not print the median rate for any score')

    args = parser.parse_args()
    return args


def get_all_rates(result_directory):
    # Init
    rates = {
        'compiler_and_sanitizer': [],
        'assertions': [],
        'cppcheck': [],
        'clang_tidy': [],
        'cyclomatic_complexity': [],
        'lizard_warnings': [],
        'unique': [],
        'kwstyle': []
    }

    # Get all the rates
    for folder in FOLDERS:
        compiler_and_sanitizer_rate, assertion_rate, cppcheck_rate, clang_tidy_rate, ccn, lizard_rate, unique_rate, \
            kwstyle_rate = calculate_score_table.get_result_rates(result_directory, folder)

        rates['compiler_and_sanitizer'].append((folder, compiler_and_sanitizer_rate))
        rates['assertions'].append((folder, assertion_rate))
        rates['cppcheck'].append((folder, cppcheck_rate))
        rates['clang_tidy'].append((folder, clang_tidy_rate))
        rates['cyclomatic_complexity'].append((folder, ccn))
        rates['lizard_warnings'].append((folder, lizard_rate))
        rates['unique'].append((folder, unique_rate))
        rates['kwstyle'].append((folder, kwstyle_rate))

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


def print_average_and_median(list_of_rates, no_average=False, no_median=False):
    if not no_average:
        average = sum(val[1] for val in list_of_rates) / len(list_of_rates)
        print('\t', 'Average:', average)

    if not no_median:
        if len(list_of_rates) % 2 == 0:  # even number of elements
            median_higher_index = int(len(list_of_rates) / 2)
            median_lower_index = median_higher_index - 1
            median = (list_of_rates[median_lower_index][1] + list_of_rates[median_higher_index][1]) / 2
        else:  # odd number of elements
            median_index = int(len(list_of_rates) / 2)
            median = list_of_rates[median_index][1]
        print('\t', 'Median:', median)

    if not (no_average and no_median):
        print()


def print_all_rates(sorted_rates, no_average=False, no_median=False):
    for rate in sorted_rates.keys():
        cur_list = sorted_rates[rate]
        print(rate + ':', '(from best to worst)')
        for val in cur_list:
            print('\t', val[1], val[0])
        print()
        print_average_and_median(cur_list, no_average, no_median)


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
    elif args.best_only:
        print_best_rates_only(sorted_rates, args.no_average, args.no_median)
    else:
        print_best_rates(sorted_rates, args.no_average, args.no_median)


if __name__ == "__main__":
    main()
