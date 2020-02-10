#!/usr/bin/env python3
"""
Calculates the code quality benchmark using scoring.py.
"""

import sys
from collections import defaultdict

import compare_results
import scoring

NA_SEQUENCE = "N/A"


def main():
    file_path = sys.argv[1]
    space_pattern = [22, 9, 16, 24, 12, 10, 12, 23, 17, 8, 9, 7]
    space_pattern_constant = [17, 8, 11, 10, 11, 12, 10, 12, 23, 17, 20, 9, 7]

    scores = defaultdict()
    scores["compiler_and_sanitizer"] = {}
    scores["assertions"] = {}
    scores["cppcheck"] = {}
    scores["clang_tidy"] = {}
    scores["cyclomatic_complexity"] = {}
    scores["lizard_warnings"] = {}
    scores["unique"] = {}
    scores["kwstyle"] = {}
    scores["infer"] = {}
    scores["overall"] = {}

    scores_absolute = defaultdict()
    scores_absolute["relative_score"] = {}
    scores_absolute["compiler_and_sanitizer"] = {}
    scores_absolute["assertions"] = {}
    scores_absolute["cppcheck"] = {}
    scores_absolute["clang_tidy"] = {}
    scores_absolute["cyclomatic_complexity"] = {}
    scores_absolute["lizard_warnings"] = {}
    scores_absolute["unique"] = {}
    scores_absolute["kwstyle"] = {}
    scores_absolute["infer"] = {}
    scores_absolute["overall"] = {}

    rates = {
        'compiler_and_sanitizer': [],
        'assertions': [],
        'cppcheck': [],
        'clang_tidy': [],
        'cyclomatic_complexity': [],
        'lizard_warnings': [],
        'unique': [],
        'kwstyle': [],
        'infer': []
    }

    d = defaultdict()
    d_absolute = defaultdict()
    constants = defaultdict()

    available_categories = {}

    # | program | overall | relative score | compiler_and_sanitizer | assertions | cppcheck | clang_tidy | cyclomatic_complexity | lizard_warnings | unique | kwstyle | infer |
    # | program | loc | functions | compiler | sanitizer | assertions | cppcheck | clang_tidy | cyclomatic_complexity | lizard_warnings | unique | kwstyle | infer |

    folder_included = []

    with open(file_path) as file:
        for line in file:
            line = line.rstrip().replace(" ", "").split("|")
            if len(line) < 14: continue

            skip_round = False
            for i in range(1, 4):  # if we can't even get the loc or function numbers, we just skip the tool
                if NA_SEQUENCE in line[i]: skip_round = True
            if skip_round: continue

            folder = line[1]
            loc = int(line[2])
            functions = int(line[3])
            compiler = int(line[4])
            sanitizer = int(line[5])

            if len(line) == 14:  # TODO: fix this, this was used to add a new category to the table
                line.append("")
                if not line[13]: line[13] = NA_SEQUENCE
            else:
                if folder in folder_included: folder_included.remove(folder)  # update old value

            if folder in folder_included: continue
            folder_included.append(folder)

            available_categories[folder] = []

            # TODO: turn this pile of shame into elegant code someday
            if NA_SEQUENCE not in line[6]:
                assertions = int(line[6])
                assertion_rate = assertions / loc
                scores['assertions'][folder] = scoring.calculate_assertion_score(assertion_rate)
                scores_absolute['assertions'][folder] = scoring.calculate_assertion_score_absolute(assertion_rate)
                available_categories[folder].append('assertions')
                rates['assertions'].append((folder, assertion_rate))

            if NA_SEQUENCE not in line[7]:
                cppcheck = int(line[7])
                cppcheck_rate = cppcheck / loc
                scores['cppcheck'][folder] = scoring.calculate_cppcheck_score(cppcheck_rate)
                scores_absolute['cppcheck'][folder] = scoring.calculate_cppcheck_score_absolute(cppcheck_rate)
                available_categories[folder].append('cppcheck')
                rates['cppcheck'].append((folder, cppcheck_rate))

            if NA_SEQUENCE not in line[8]:
                clang_tidy = int(line[8])
                clang_tidy_rate = clang_tidy / loc
                scores['clang_tidy'][folder] = scoring.calculate_clang_tidy_score(clang_tidy_rate)
                scores_absolute['clang_tidy'][folder] = scoring.calculate_clang_tidy_score_absolute(clang_tidy_rate)
                available_categories[folder].append('clang_tidy')
                rates['clang_tidy'].append((folder, clang_tidy_rate))

            if NA_SEQUENCE not in line[9]:
                cyclomatic_complexity = float(line[9])
                ccn = cyclomatic_complexity
                scores['cyclomatic_complexity'][folder] = scoring.calculate_cyclomatic_complexity_score(ccn)
                scores_absolute['cyclomatic_complexity'][
                    folder] = scoring.calculate_cyclomatic_complexity_score_absolute(ccn)
                available_categories[folder].append('cyclomatic_complexity')
                rates['cyclomatic_complexity'].append((folder, ccn))

            if NA_SEQUENCE not in line[10]:
                lizard_warnings = int(line[10])
                lizard_rate = lizard_warnings / functions
                scores['lizard_warnings'][folder] = scoring.calculate_lizard_warning_score(lizard_rate)
                scores_absolute['lizard_warnings'][folder] = scoring.calculate_lizard_warning_score_absolute(
                    lizard_rate)
                available_categories[folder].append('lizard_warnings')
                rates['lizard_warnings'].append((folder, lizard_rate))

            if NA_SEQUENCE not in line[11]:
                unique = float(line[11])
                unique_rate = unique
                scores['unique'][folder] = scoring.calculate_unique_score(unique_rate)
                scores_absolute['unique'][folder] = scoring.calculate_unique_score_absolute(unique_rate)
                available_categories[folder].append('unique')
                rates['unique'].append((folder, unique_rate))

            if NA_SEQUENCE not in line[12]:
                kwstyle = int(line[12])
                kwstyle_rate = kwstyle / loc
                scores['kwstyle'][folder] = scoring.calculate_kwstyle_score(kwstyle_rate)
                scores_absolute['kwstyle'][folder] = scoring.calculate_kwstyle_score_absolute(kwstyle_rate)
                available_categories[folder].append('kwstyle')
                rates['kwstyle'].append((folder, kwstyle_rate))

            if NA_SEQUENCE not in line[13]:
                infer = int(line[13])
                infer_rate = infer / loc
                scores['infer'][folder] = scoring.calculate_infer_score(infer_rate)
                scores_absolute['infer'][folder] = scoring.calculate_infer_score_absolute(infer_rate)
                available_categories[folder].append('infer')
                rates['infer'].append((folder, infer_rate))

            compiler_and_sanitizer_rate = (compiler + sanitizer) / loc
            scores['compiler_and_sanitizer'][folder] = scoring.calculate_compiler_and_sanitizer_score(
                compiler_and_sanitizer_rate)
            scores_absolute['compiler_and_sanitizer'][folder] = scoring.calculate_compiler_and_sanitizer_score_absolute(
                compiler_and_sanitizer_rate)
            available_categories[folder].append('compiler_and_sanitizer')
            rates['compiler_and_sanitizer'].append((folder, compiler_and_sanitizer_rate))

            list_of_scores = [scores[score][folder] for score in scores.keys()
                              if score != 'overall' and score in available_categories[folder]]
            scores['overall'][folder] = scoring.average_score(list_of_scores)

            scores_absolute['relative_score'][folder] = scores['overall'][folder]
            available_categories[folder].append('relative_score')

            list_of_scores = [scores_absolute[score][folder] for score in scores_absolute.keys()
                              if score != 'overall' and score != 'relative_score'
                              and score in available_categories[folder]]
            scores_absolute['overall'][folder] = scoring.average_score(list_of_scores)

            d[folder] = scores['overall'][folder]
            d_absolute[folder] = scores_absolute['overall'][folder]

            constants[folder] = line[1:-1]

    sorted_list = sorted(d.items(), key=lambda x: x[1], reverse=True)
    sorted_list_absolute = sorted(d_absolute.items(), key=lambda x: x[1], reverse=True)

    sorted_list_constants = sorted(constants.items(), key=lambda x: int(x[1][1]), reverse=True)

    for (name, score) in sorted_list_constants:
        print("|", end="")
        counter = 0
        for index in constants[name]:
            print(" {}".format(index).ljust(space_pattern_constant[counter]), end="|")
            counter += 1
        print()
    print()


    for (name, score) in sorted_list_absolute:
        score_absolute = scores_absolute['overall'][name]
        print("| {}".format(name).ljust(space_pattern[0]), end="|")
        print(" {}".format(round(score_absolute, 1)).ljust(space_pattern[1]), end="|")
        counter = 2

        for key in scores_absolute.keys():
            if key == 'overall': continue

            if key not in available_categories[name]:
                print((" " + NA_SEQUENCE).ljust(space_pattern[counter]), end="|")
            else:
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
    rc = 1 - (6 * rc_d_squared_sum / (n * (n * n - 1)))
    print("Rank correlation: {}".format(rc))

    sorted_rates = compare_results.sort_rates(rates)
    print()
    compare_results.print_best_rates(sorted_rates)
    compare_results.print_softwipe_scoring_values(sorted_rates)

    return 0


if __name__ == "__main__":
    main()
