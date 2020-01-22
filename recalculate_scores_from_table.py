#!/usr/bin/env python3
"""
Calculates the code quality benchmark using scoring.py.
"""

import os
import sys
import scoring
from collections import defaultdict


def main():
    file_path = sys.argv[1]
    space_pattern = [22, 19, 24, 12, 10, 12, 23, 17, 8, 9, 7]   #TODO: space_pattern[1] should be 9

    record = False      #need to filter the first few lines in case there is some unnecessary log data there
    data = []

    scores = {
        'overall': {},
        'compiler_and_sanitizer': {},
        'assertions': {},
        'cppcheck': {},
        'clang_tidy': {},
        'cyclomatic_complexity': {},
        'lizard_warnings': {},
        'unique': {},
        'kwstyle': {},
        # 'infer': {},   #TODO: add this again
    }

    scores = defaultdict()
    scores["compiler_and_sanitizer"] = {}
    scores["assertions"] = {}
    scores["cppcheck"] = {}
    scores["clang_tidy"] = {}
    scores["cyclomatic_complexity"] = {}
    scores["lizard_warnings"] = {}
    scores["unique"] = {}
    scores["kwstyle"] = {}
    #scores["infer"] = {}
    scores["overall"] = {}

    scores_absolute = defaultdict()
    scores_absolute["compiler_and_sanitizer"] = {}
    scores_absolute["assertions"] = {}
    scores_absolute["cppcheck"] = {}
    scores_absolute["clang_tidy"] = {}
    scores_absolute["cyclomatic_complexity"] = {}
    scores_absolute["lizard_warnings"] = {}
    scores_absolute["unique"] = {}
    scores_absolute["kwstyle"] = {}
    # scores_absolute["infer"] = {}
    scores_absolute["overall"] = {}

    d = defaultdict()
    d_absolute = defaultdict()

    rc_d_squared = {}

    sorted_list = []
    sorted_list_absolute = []

    #| program | overall | compiler_and_sanitizer | assertions | cppcheck | clang_tidy | cyclomatic_complexity | lizard_warnings | unique | kwstyle |
    #| program | loc | functions | compiler | sanitizer | assertions | cppcheck | clang_tidy | cyclomatic_complexity | lizard_warnings | unique | kwstyle |

    with open(file_path) as file:
        for line in file:
            line = line.rstrip().replace(" ", "").split("|")

            folder = line[1]
            loc = int(line[2])
            functions = int(line[3])
            compiler = int(line[4])
            sanitizer = int(line[5])
            assertions = int(line[6])
            cppcheck = int(line[7])
            clang_tidy = int(line[8])
            cyclomatic_complexity = float(line[9])
            lizard_warnings = int(line[10])
            unique = float(line[11])
            kwstyle = int(line[12])

            compiler_and_sanitizer_rate = (compiler + sanitizer) / loc
            assertion_rate = assertions / loc
            cppcheck_rate = cppcheck / loc
            clang_tidy_rate = clang_tidy / loc
            ccn = cyclomatic_complexity
            lizard_rate = lizard_warnings / functions
            unique_rate = unique
            kwstyle_rate = kwstyle / loc

            scores['compiler_and_sanitizer'][folder] = scoring.calculate_compiler_and_sanitizer_score(
                compiler_and_sanitizer_rate)
            scores['assertions'][folder] = scoring.calculate_assertion_score(assertion_rate)
            scores['cppcheck'][folder] = scoring.calculate_cppcheck_score(cppcheck_rate)
            scores['clang_tidy'][folder] = scoring.calculate_clang_tidy_score(clang_tidy_rate)
            scores['cyclomatic_complexity'][folder] = scoring.calculate_cyclomatic_complexity_score(ccn)
            scores['lizard_warnings'][folder] = scoring.calculate_lizard_warning_score(lizard_rate)
            scores['unique'][folder] = scoring.calculate_unique_score(unique_rate)
            scores['kwstyle'][folder] = scoring.calculate_kwstyle_score(kwstyle_rate)
            # scores['infer'][folder] = scoring.calculate_infer_score(infer_rate)    #TODO: add this again

            scores_absolute['compiler_and_sanitizer'][folder] = scoring.calculate_compiler_and_sanitizer_score_absolute(
                compiler_and_sanitizer_rate)
            scores_absolute['assertions'][folder] = scoring.calculate_assertion_score_absolute(assertion_rate)
            scores_absolute['cppcheck'][folder] = scoring.calculate_cppcheck_score_absolute(cppcheck_rate)
            scores_absolute['clang_tidy'][folder] = scoring.calculate_clang_tidy_score_absolute(clang_tidy_rate)
            scores_absolute['cyclomatic_complexity'][folder] = scoring.calculate_cyclomatic_complexity_score_absolute(ccn)
            scores_absolute['lizard_warnings'][folder] = scoring.calculate_lizard_warning_score_absolute(lizard_rate)
            scores_absolute['unique'][folder] = scoring.calculate_unique_score_absolute(unique_rate)
            scores_absolute['kwstyle'][folder] = scoring.calculate_kwstyle_score_absolute(kwstyle_rate)
            # scores['infer'][folder] = scoring.calculate_infer_score_absolute(infer_rate)    #TODO: add this again

            list_of_scores = [scores[score][folder] for score in scores.keys() if score != 'overall']
            scores['overall'][folder] = scoring.average_score(list_of_scores)

            list_of_scores = [scores_absolute[score][folder] for score in scores_absolute.keys() if score != 'overall']
            scores_absolute['overall'][folder] = scoring.average_score(list_of_scores)

            d[folder] = scores['overall'][folder]
            d_absolute[folder] = scores_absolute['overall'][folder]



    sorted_list = sorted(d.items(), key = lambda x: x[1], reverse=True)
    sorted_list_absolute = sorted(d_absolute.items(), key = lambda x: x[1], reverse=True)




    for (name, score) in sorted_list:
        score_absolute = scores_absolute['overall'][name]
        print("| {}".format(name).ljust(space_pattern[0]), end="|")
        print(" {} - {}".format(round(score, 4), round(score_absolute, 4)).ljust(space_pattern[1]), end="|")
        counter = 2
        '''for i in range(0, len(TOOL_KEYS)):
            key = TOOL_KEYS[i]
            print(" {0:0.1f}".format(round(scores[key][name], 1)).ljust(space_pattern[counter]), end="|")
            counter += 1
        '''
        for key in scores_absolute.keys():
            if key == 'overall': continue
            print(" {0:0.1f}".format(round(scores_absolute[key][name], 1)).ljust(space_pattern[counter]), end="|")
            counter += 1
        print()


    counter = 0
    rc_d_squared_sum = 0
    for (name, _) in sorted_list:
        counter2 = 0
        for (name2, _) in sorted_list_absolute:
            if name == name2:
                rc_d_squared_sum += (counter - counter2) * (counter - counter2)
            counter2 += 1
        counter += 1
    n = counter
    rc = 1 - (6 * rc_d_squared_sum / (n * (n*n - 1)))
    print("Rank correlation: {}".format(rc))

    #print("{}: {}".format(folder, scores["overall"][folder]))

    return 0


if __name__ == "__main__":
    main()
