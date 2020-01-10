#!/usr/bin/env python3
"""
Calculates the code quality benchmark using scoring.py.
"""

import os
import sys
import scoring



def main():
    file_path = sys.argv[1]

    record = False      #need to filter the first few lines in case there is some unnecessary log data there
    data = []

    scores = {
        'compiler_and_sanitizer': {},
        'assertions': {},
        'cppcheck': {},
        'clang_tidy': {},
        'cyclomatic_complexity': {},
        'lizard_warnings': {},
        'unique': {},
        'kwstyle': {},
        'overall': {}
    }

    with open(file_path) as file:
        for line in file:
            if record:
                data.append(line.replace("\n", ""))
                line = line.replace("\n", "")
                folder, loc, functions, compiler_warnings, sanitizer_warnings, assertions, cppcheck_warnings, clang_tidy_warnings, \
                ccn, lizard_warnings, unique, kwstyle_warnings = line.split(",")
                loc = float(loc)

                scores['compiler_and_sanitizer'][folder] = scoring.calculate_compiler_and_sanitizer_score(float(compiler_warnings + sanitizer_warnings)/loc) #TODO: fix this
                scores['assertions'][folder] = scoring.calculate_assertion_score(float(assertions)/loc)
                scores['cppcheck'][folder] = scoring.calculate_cppcheck_score(float(cppcheck_warnings)/loc)
                scores['clang_tidy'][folder] = scoring.calculate_clang_tidy_score(float(clang_tidy_warnings)/loc)
                scores['cyclomatic_complexity'][folder] = scoring.calculate_cyclomatic_complexity_score(float(ccn))
                scores['lizard_warnings'][folder] = scoring.calculate_lizard_warning_score(float(lizard_warnings)/loc)
                scores['unique'][folder] = scoring.calculate_unique_score(float(unique))
                scores['kwstyle'][folder] = scoring.calculate_kwstyle_score(float(kwstyle_warnings)/loc)

                # Calculate the overall score
                list_of_scores = [scores[score][folder] for score in scores.keys() if score != 'overall']
                scores['overall'][folder] = scoring.average_score(list_of_scores)

                #print(folder + " {}".format(scores['overall'][folder]))


            if "program" in line:
                record = True
    print(scores)
    return 0


if __name__ == "__main__":
    main()
