#!/usr/bin/env python3
"""
Calculates the code quality benchmark using scoring.py.
This script parses the rates from files containing the output of softwipe for each program that should be included in
the benchmark. It then recalculates the scores according to the current scoring.py. Then, it prints a csv containing
all scores.
"""

import argparse
import os
import scoring


###########################################################
# If you add a new program to the benchmark, add the name #
# of its folder in the results directory to this list!    #
###########################################################
FOLDERS = ['dawg', 'mrbayes', 'raxml-ng', 'sf', 'hyperphylo', 'kahypar', 'ms', 'repeatscounter', 'tcoffee', 'bpp',
           'indelible', 'mafft', 'prank', 'seq-gen', 'genesis', 'athena', 'gadget', 'iqtree', 'clustal', 'phyml',
           'minimap', 'samtools', 'vsearch', 'swarm', 'cellcoal', 'treerecs']
#SOFTWIPE_OUTPUT_FILE_NAME = 'softwipe_output.txt'
SOFTWIPE_OUTPUT_FILE_NAME = "sw_batch.txt"

#For the prototype
SW_REL_FILE_NAME = "sw_batch.txt"
SW_ABS_FILE_NAME = "sw_batch.txt"


def parse_arguments():
    parser = argparse.ArgumentParser(description="Calculate the code quality benchmark (i.e., the scores) and output "
                                                 "a csv containing all scores.")
    parser.add_argument('result_directory', nargs=1, help='the directory where all result folders are saved in. For '
                                                          'each program that should be included in the benchmark, '
                                                          'a folder should exist in this directory that contains the '
                                                          'output of softwipe in a file called '
                                                          '"' + SOFTWIPE_OUTPUT_FILE_NAME + '"')
    parser.add_argument('-A', '--absolute', action='store_true', help='create a table with absolute values rather '
                                                                      'than scores')
    #parser.add_argument('-o', help='output file to store the scores')
    parser.add_argument('--only-overall-scores', action='store_true', help='flag only implemented for easier comparison of different '
                                                      'scoring techniques')

    args = parser.parse_args()
    return args


def get_result_rates(result_directory, folder):
    cur_folder = os.path.join(result_directory, folder)
    cur_file = os.path.join(cur_folder, SOFTWIPE_OUTPUT_FILE_NAME)
    cur_lines = open(cur_file, 'r').readlines()  # Softwipe output lines

    # Init
    compiler_and_sanitizer_rate = 0.0  # Special treatment because we may have to add multiple values for this score
    assertion_rate = cppcheck_rate = clang_tidy_rate = ccn = lizard_rate = unique_rate = kwstyle_rate = infer_rate = None

    infer_rate = -1

    # Iterate through the softwipe output
    for line in cur_lines:
        split_line = line.split()

        # Compiler and sanitizer rate treatment
        if line.startswith('Weighted compiler warning rate:'):
            compiler_and_sanitizer_rate += float(split_line[4])
        elif line.startswith(('AddressSanitizer error rate:', 'UndefinedBehaviorSanitizer error rate:')):
            compiler_and_sanitizer_rate += float(split_line[3])

        # All other rates
        elif line.startswith('Assertion rate:'):
            assertion_rate = float(split_line[2])
        elif line.startswith('Total weighted Cppcheck warning rate:'):
            cppcheck_rate = float(split_line[5])
        elif line.startswith('Weighted Clang-tidy warning rate:'):
            clang_tidy_rate = float(split_line[4])
        elif line.startswith('Average cyclomatic complexity:'):
            ccn = float(split_line[3])
        elif line.startswith('Lizard warning rate (~= rate of functions that are too complex):'):
            lizard_rate = float(split_line[11])
        elif line.startswith('Unique code rate:'):
            unique_rate = float(split_line[3])
        elif line.startswith('KWStyle warning rate:'):
            kwstyle_rate = float(split_line[3])
        elif line.startswith('Weighted Infer warning rate:'):
            infer_rate = float(split_line[4])

    return compiler_and_sanitizer_rate, assertion_rate, cppcheck_rate, clang_tidy_rate, ccn, lizard_rate, \
        unique_rate, kwstyle_rate, infer_rate


def get_result_values(result_directory, folder):
    def get_absolute_value(abs_by_loc):
        return int(abs_by_loc.split('/')[0][1:])

    cur_folder = os.path.join(result_directory, folder)
    cur_file = os.path.join(cur_folder, SOFTWIPE_OUTPUT_FILE_NAME)
    cur_lines = open(cur_file, 'r').readlines()  # Softwipe output lines

    # Init
    sanitizer_warnings = 0
    loc = functions = compiler_warnings = assertions = cppcheck_warnings = clang_tidy_warnings = \
        ccn = lizard_warnings = unique = kwstyle_warnings = None

    # Iterate through the softwipe output
    for line in cur_lines:
        split_line = line.split()

        if line.startswith('Lines of pure'):
            loc = int(split_line[-1])
        elif line.startswith('Weighted compiler warning rate:'):
            compiler_warnings = get_absolute_value(split_line[-1])
        elif line.startswith(('AddressSanitizer error rate:', 'UndefinedBehaviorSanitizer error rate:')):
            sanitizer_warnings += get_absolute_value(split_line[-1])
        elif line.startswith('Assertion rate:'):
            assertions = get_absolute_value(split_line[-1])
        elif line.startswith('Total weighted Cppcheck warning rate:'):
            cppcheck_warnings = get_absolute_value(split_line[-1])
        elif line.startswith('Weighted Clang-tidy warning rate:'):
            clang_tidy_warnings = get_absolute_value(split_line[-1])
        elif line.startswith('Average cyclomatic complexity:'):
            ccn = float(split_line[-1])
        elif line.startswith('Lizard warning rate (~= rate of functions that are too complex):'):
            functions = int(split_line[-1].split('/')[1][:-1])
            lizard_warnings = get_absolute_value(split_line[-1])
        elif line.startswith('Unique code rate:'):
            unique = float(split_line[-1])
        elif line.startswith('KWStyle warning rate:'):
            kwstyle_warnings = get_absolute_value(split_line[-1])

    return loc, functions, compiler_warnings, sanitizer_warnings, assertions, cppcheck_warnings, clang_tidy_warnings, \
                ccn, lizard_warnings, unique, kwstyle_warnings

#TODO: this is just a prototype for now
def find_sw_scores(path):
    f = []
    d = []
    for (_, dirname, filename) in os.walk(path):
        f.extend(filename)
        d.extend(dirname)
        break
    if SW_REL_FILE_NAME in f:
        FOLDERS.append(path)
        return

    for dir in d:
        find_sw_scores(path + "/" + dir)

def calculate_scores(result_directory, absolute):
    # Init
    if absolute:
        scores = {
            'loc': {},
            'functions': {},
            'compiler': {},
            'sanitizer': {},
            'assertions': {},
            'cppcheck': {},
            'clang_tidy': {},
            'cyclomatic_complexity': {},
            'lizard_warnings': {},
            'unique': {},
            'kwstyle': {}
        }
    else:
        scores = {
            'compiler_and_sanitizer': {},
            'assertions': {},
            'cppcheck': {},
            'clang_tidy': {},
            'cyclomatic_complexity': {},
            'lizard_warnings': {},
            'unique': {},
            'kwstyle': {},
            #'infer': {},   #TODO: add this again
            'overall': {}
        }

    #Slightly change the way the tool folders are found
    print(result_directory)
    dirs = []
    FOLDERS.clear()

    for (_, dirname, _) in os.walk(result_directory):
        dirs.extend(dirname)
        break
    for dir in dirs:
        find_sw_scores(result_directory + "/" + dir)

    temp = [e.replace(result_directory + "/", "") for e in FOLDERS]
    FOLDERS.clear()
    FOLDERS.extend(temp)
    #FOLDERS = temp
    print(FOLDERS)

    FOLDERS.clear()
    #FOLDERS.extend(['BGSA-1.0/original/BGSA_SSE', 'bindash-1.0', 'copmem-0.2', 'crisflash', 'cryfa-18.06', 'defor', 'dna-nn-0.1', 'dr_sasa_n', 'emeraLD', 'ExpansionHunter', 'fastspar', 'HLA-LA/src', 'lemon', 'naf-1.1.0/ennaf', 'naf-1.1.0/unnaf', 'ngsTools/ngsLD', 'ntEdit-1.2.3', 'PopLDdecay', 'virulign-1.0.1', 'axe-0.3.3', 'prequal', 'IQ-TREE-2.0-rc1']) #TODO: add SPRING
    FOLDERS.extend(['IQ-TREE-2.0-rc1'])

    for score in scores:
        for folder in FOLDERS:
            scores[score][folder] = None

    # Get all the scores
    for folder in FOLDERS:
        if absolute:
            # Get values
            loc, functions, compiler_warnings, sanitizer_warnings, assertions, cppcheck_warnings, clang_tidy_warnings, \
                ccn, lizard_warnings, unique, kwstyle_warnings = get_result_values(result_directory, folder)
            scores['loc'][folder] = loc
            scores['functions'][folder] = functions
            scores['compiler'][folder] = compiler_warnings
            scores['sanitizer'][folder] = sanitizer_warnings
            scores['assertions'][folder] = assertions
            scores['cppcheck'][folder] = cppcheck_warnings
            scores['clang_tidy'][folder] = clang_tidy_warnings
            scores['cyclomatic_complexity'][folder] = ccn
            scores['lizard_warnings'][folder] = lizard_warnings
            scores['unique'][folder] = unique
            scores['kwstyle'][folder] = kwstyle_warnings
        else:
            # Get rates
            compiler_and_sanitizer_rate, assertion_rate, cppcheck_rate, clang_tidy_rate, ccn, lizard_rate, \
                unique_rate, kwstyle_rate, infer_rate = get_result_rates(result_directory, folder)

            print(folder + " infer rate: {}".format(infer_rate))

            # Get scores
            scores['compiler_and_sanitizer'][folder] = scoring.calculate_compiler_and_sanitizer_score(
                compiler_and_sanitizer_rate)
            scores['assertions'][folder] = scoring.calculate_assertion_score(assertion_rate)
            scores['cppcheck'][folder] = scoring.calculate_cppcheck_score(cppcheck_rate)
            scores['clang_tidy'][folder] = scoring.calculate_clang_tidy_score(clang_tidy_rate)
            scores['cyclomatic_complexity'][folder] = scoring.calculate_cyclomatic_complexity_score(ccn)
            scores['lizard_warnings'][folder] = scoring.calculate_lizard_warning_score(lizard_rate)
            scores['unique'][folder] = scoring.calculate_unique_score(unique_rate)
            scores['kwstyle'][folder] = scoring.calculate_kwstyle_score(kwstyle_rate)
            #scores['infer'][folder] = scoring.calculate_infer_score(infer_rate)    #TODO: add this again

            # Calculate the overall score
            list_of_scores = [scores[score][folder] for score in scores.keys() if score != 'overall']
            scores['overall'][folder] = scoring.average_score(list_of_scores)

    return scores


def print_score_csv(scores, absolute, print_only_overall):
    last_column = 'kwstyle' if absolute else 'overall'

    print('program', end=',')
    for score in scores:
        if score != last_column:
            print(score, end=',')
        else:
            print(score)
    for folder in FOLDERS:
        if not print_only_overall:
            print(folder, end=',')
            for score in scores:
                if score != last_column:
                    print(scores[score][folder], end=',')
                else:
                    print(scores[score][folder])
        else:
            #print(folder, end=" ")
            print(round(scores['overall'][folder], 1))


def main():
    args = parse_arguments()
    result_directory = os.path.abspath(args.result_directory[0])
    absolute = True if args.absolute else False
    print_only_overall = True if args.only_overall_scores else False
    scores = calculate_scores(result_directory, absolute)
    print_score_csv(scores, absolute, print_only_overall)


if __name__ == "__main__":
    main()
