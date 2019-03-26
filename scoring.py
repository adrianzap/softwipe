"""
Functions for calculating the scores for each category that is checked by softwipe.
"""


def print_score(score, score_name=None):
    """
    Print a score, rounding it to 1 decimal.
    :param score: The score to print.
    :param score_name: Give the score a name which will be printed as well.
    """
    print(score_name, 'Score: {0:.1f}/10'.format(round(score, 1)))
    print()


def average_score(list_of_scores):
    """
    Calculate an average score over a list of scores.
    :param list_of_scores: A list containing all scores to average over.
    :return: The average score.
    """
    avg = sum(list_of_scores) / float(len(list_of_scores))
    return avg


def _calculate_score_generic(rate, best, worst):
    """
    Calculates a score from 0 to 10 from a rate, given the best and worst rates. This is a generic function that
    should be called by all other functions. If best > worst, it is assumed that higher is better, else it is assumed
    that lower is better.
    :param rate: The rate for which a score should be calculated.
    :param best: The rate for which a 10/10 score should be yielded.
    :param worst: The rate for which a 0/10 score should be yielded.
    :return: A score between 0 and 10.
    """
    # The following can be seen as a linear function f where f(worst) = 0 and f(best) = 10. Simple math yields this
    # exact formula. The slope of this function (10/(best-worst)) is positive if best > worst and negative if worst >
    # best. Thus, this function works as intended in both cases.
    score = (10 * rate) / (best - worst) - (10 * worst) / (best - worst)
    # The linear function produces scores < 0 and > 10 if rate is worse than worst or better than best, respectively.
    # Thus, the score value needs to be corrected.
    if score > 10:
        score = 10
    elif score < 0:
        score = 0

    return score


# CONSTANTS TO BE USED BY THE CALCULATION FUNCTIONS

COMPILER_BEST = 0.028
COMPILER_WORST = 0.57

SANITIZER_BEST = 0
SANITIZER_WORST = 0.0002  # TODO Maybe add the sanitizer rate to the compiler rate as level 3 warnings?

ASSERTIONS_BEST = 0.034
ASSERTIONS_WORST = 0

CPPCHECK_BEST = 0.001
CPPCHECK_WORST = 0.1

CLANG_TIDY_BEST = 0.001
CLANG_TIDY_WORST = 0.27

CYCLOMATIC_COMPLEXITY_BEST = 1.7
CYCLOMATIC_COMPLEXITY_WORST = 22.2

LIZARD_WARNINGS_BEST = 0
LIZARD_WARNINGS_WORST = 0.3

DUPLICATE_BEST = 0.027
DUPLICATE_WORST = 2.57

UNIQUE_BEST = 0.98
UNIQUE_WORST = 0.81

KWSTYLE_BEST = 0.002
KWSTYLE_WORST = 1.6


# FUNCTIONS THAT CALCULATE THE SCORES

def calculate_compiler_score(rate):
    return _calculate_score_generic(rate, COMPILER_BEST, COMPILER_WORST)


def calculate_sanitizer_score(rate):
    return _calculate_score_generic(rate, SANITIZER_BEST, SANITIZER_WORST)


def calculate_assertion_score(rate):
    return _calculate_score_generic(rate, ASSERTIONS_BEST, ASSERTIONS_WORST)


def calculate_cppcheck_score(rate):
    return _calculate_score_generic(rate, CPPCHECK_BEST, CPPCHECK_WORST)


def calculate_clang_tidy_score(rate):
    return _calculate_score_generic(rate, CLANG_TIDY_BEST, CLANG_TIDY_WORST)


def calculate_cyclomatic_complexity_score(ccn):
    return _calculate_score_generic(ccn, CYCLOMATIC_COMPLEXITY_BEST, CYCLOMATIC_COMPLEXITY_WORST)


def calculate_lizard_warning_score(rate):
    return _calculate_score_generic(rate, LIZARD_WARNINGS_BEST, LIZARD_WARNINGS_WORST)


def calculate_duplicate_score(rate):
    return _calculate_score_generic(rate, DUPLICATE_BEST, DUPLICATE_WORST)


def calculate_unique_score(rate):
    return _calculate_score_generic(rate, UNIQUE_BEST, UNIQUE_WORST)


def calculate_kwstyle_score(rate):
    return _calculate_score_generic(rate, KWSTYLE_BEST, KWSTYLE_WORST)
