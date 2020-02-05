"""
Functions for calculating the scores for each category that is checked by softwipe.
"""
import math
import numpy as np      #TODO: maybe remove numpy dependency
from scipy.optimize import curve_fit

def print_score(score, score_name=None):
    """
    Print a score, rounding it to 1 decimal.
    :param score: The score to print.
    :param score_name: Give the score a name which will be printed as well.
    """
    print(get_score_string(score, score_name))
    print()

def get_score_string(score, score_name=""):
    return score_name + ' Score: {0:.1f}/10'.format(round(score, 1))


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


def _calculate_score_absolute(rate, best, worst, case=0):
    return _calculate_score_curve_fit_combined(rate, best, worst, case=case)



def _calculate_score_smooth_linear(rate, best, worst, case=0):
    """
    Calculates an absolute score with regard to some best and worst rates but stays within the 0-10 score range if
    rate is outside of the [worst, best] interval (which is a problematic case when using _calculate_score_generic()).
    There evaluation function is split in 3 parts. The mid part is always linear. The left and right parts are chosen
    based on the analysis tool used. For example: If we don't know the absolute worst and best rates an analysis tool
    produces, we use the sigmoid function to approach the max. and min. scores for rates outside of the [worst, best]
    interval (this is 'case 0'). For usages like the counting of warnings, we assume that the best scenario is
    'no warnings' - 0, so we can approach this value linearly using the 'case 1'.
    To achieve the 'case 0' scoring, we set a value v (e.g. 9.5) that is to be yielded if rate = best and the value
    (10-v) that is to be yielded if rate = worst. Rates in [0.5, 9.5] score range are scaled linearly, scores outside
    that range are scaled using parts of the sigmoid function.

    :param rate: The rate for which a score should be calculated.
    :param best: The rate for which a v/10 should be yielded
    :param worst: The rate for which a (10-v)/10 score should be yielded.
    :param case: The case covers different possibilities to assemble the evaluation function
        case 0: sigmoid  - linear - sigmoid
        case 1: sigmoid  - linear - constant
        case 2: constant - linear - sigmoid
    """

    d = best - worst;
    x = (rate - worst)

    if x / d <= 0:  # approach the 0 with a sigmoid
        if case != 2:
            k = (np.log(1 / 0.01 - 1) - np.log(1 / 0.05 - 1)) / d
            x0 = np.log(1 / 0.05 - 1) / k
            return 10 * sigmoid(x, x0, k)
        else:
            return 0
    elif x / d >= 1:  # approach the 10 with a sigmoid
        if case != 1:
            k = (np.log(1 / 0.95 - 1) - np.log(1 / 0.99 - 1)) / d
            x0 = np.log(1 / 0.95 - 1) / k + d
            return 10 * sigmoid(x, x0, k)
        else:
            return 10
    else:  # use a linear function for the middle part of the evaluation function
        if case == 0:
            a = 0.9 / d
            b = 0.05
        elif case == 1:
            a = 0.95 / d
            b = 0.05
        else:
            a = 0.95 / d
            b = 0
        return 10 * (a * x + b)


def _calculate_score_curve_fit(rate, best, worst):
    d = best - worst
    x = rate - worst
    thresh = 0.90
    xval = [(1-thresh) * d, 0.25 * d, 0.5 * d, 0.75 * d, thresh * d]
    yval = [    (1-thresh),     0.25,     0.5,     0.75,    thresh]
    popt, pcov = curve_fit(sigmoid, xval, yval)

    return 10 * sigmoid(x, *popt)


def _calculate_score_curve_fit_combined(rate, best, worst, case=0):
    d = best - worst
    x = rate - worst
    if case == 0:
        return _calculate_score_curve_fit(rate, best, worst)
    if case == 1:
        if x/d >= 1: return 10
        if x/d > 0.5:
            return 10 * (x/d)
        else:
            return _calculate_score_curve_fit(rate, best, worst)
    if case == 2:
        if x/d <= 0: return 0
        if x/d < 0.5:
            return 10 * (x/d)
        else:
            return _calculate_score_curve_fit(rate, best, worst)


def sigmoid(x, x0, k):
    y = 1 / (1 + np.exp(-k * (x - x0)))
    return y


# CONSTANTS TO BE USED BY THE CALCULATION FUNCTIONS

'''
#old values

COMPILER_BEST = 0.0
COMPILER_WORST = 0.5664638548004538

ASSERTIONS_BEST = 0.015508042681955726
ASSERTIONS_WORST = 0.0

CPPCHECK_BEST = 0.001226241569589209
CPPCHECK_WORST = 0.05527096252359127

CLANG_TIDY_BEST = 0.011649294911097487
CLANG_TIDY_WORST = 0.3600673258994319

CYCLOMATIC_COMPLEXITY_BEST = 2.4
CYCLOMATIC_COMPLEXITY_WORST = 15.1

LIZARD_WARNINGS_BEST = 0.0
LIZARD_WARNINGS_WORST = 0.3181818181818182

UNIQUE_BEST = 0.9839
UNIQUE_WORST = 0.8147

KWSTYLE_BEST = 0.0
KWSTYLE_WORST = 0.05577889447236181

INFER_BEST = 0.0
INFER_WORST = 0.005593288054334798'''

COMPILER_BEST = 0.0
COMPILER_WORST = 0.5664638548004538

ASSERTIONS_BEST = 0.015508042681955726
ASSERTIONS_WORST = 0.0

CPPCHECK_BEST = 0.0006172839506172839
CPPCHECK_WORST = 0.05527096252359127

CLANG_TIDY_BEST = 0.0
CLANG_TIDY_WORST = 0.2850356294536817

CYCLOMATIC_COMPLEXITY_BEST = 1.8
CYCLOMATIC_COMPLEXITY_WORST = 14.7

LIZARD_WARNINGS_BEST = 0.0
LIZARD_WARNINGS_WORST = 0.20833333333333334

UNIQUE_BEST = 0.9966
UNIQUE_WORST = 0.8147

KWSTYLE_BEST = 0.0
KWSTYLE_WORST = 0.07676685621445979

INFER_BEST = 0.0
INFER_WORST = 0.006405693950177936


COMPILER_BEST_FIXED = 0.0
COMPILER_WORST_FIXED = 0.5664638548004538

ASSERTIONS_BEST_FIXED = 0.015508042681955726
ASSERTIONS_WORST_FIXED = 0.0

CPPCHECK_BEST_FIXED = 0.0006172839506172839
CPPCHECK_WORST_FIXED = 0.05527096252359127

CLANG_TIDY_BEST_FIXED = 0.0
CLANG_TIDY_WORST_FIXED = 0.2850356294536817

CYCLOMATIC_COMPLEXITY_BEST_FIXED = 1.8
CYCLOMATIC_COMPLEXITY_WORST_FIXED = 14.7

LIZARD_WARNINGS_BEST_FIXED = 0.0
LIZARD_WARNINGS_WORST_FIXED = 0.20833333333333334

UNIQUE_BEST_FIXED = 0.9966
UNIQUE_WORST_FIXED = 0.8147

KWSTYLE_BEST_FIXED = 0.0
KWSTYLE_WORST_FIXED = 0.07676685621445979

INFER_BEST_FIXED = 0.0
INFER_WORST_FIXED = 0.006405693950177936




# FUNCTIONS THAT CALCULATE THE SCORES

def calculate_compiler_and_sanitizer_score(rate):
    return _calculate_score_generic(rate, COMPILER_BEST, COMPILER_WORST)


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


def calculate_unique_score(rate):
    return _calculate_score_generic(rate, UNIQUE_BEST, UNIQUE_WORST)


def calculate_kwstyle_score(rate):
    return _calculate_score_generic(rate, KWSTYLE_BEST, KWSTYLE_WORST)


def calculate_infer_score(rate):
    return _calculate_score_generic(rate, INFER_BEST, INFER_WORST)




def calculate_compiler_and_sanitizer_score_absolute(rate):
    return _calculate_score_absolute(rate, COMPILER_BEST_FIXED, COMPILER_WORST_FIXED, case=1)


def calculate_assertion_score_absolute(rate):
    return _calculate_score_absolute(rate, ASSERTIONS_BEST_FIXED, ASSERTIONS_WORST_FIXED, case=2)


def calculate_cppcheck_score_absolute(rate):
    return _calculate_score_absolute(rate, CPPCHECK_BEST_FIXED, CPPCHECK_WORST_FIXED)


def calculate_clang_tidy_score_absolute(rate):
    return _calculate_score_absolute(rate, CLANG_TIDY_BEST_FIXED, CLANG_TIDY_WORST_FIXED)


def calculate_cyclomatic_complexity_score_absolute(ccn):
    return _calculate_score_absolute(ccn, CYCLOMATIC_COMPLEXITY_BEST_FIXED, CYCLOMATIC_COMPLEXITY_WORST_FIXED)


def calculate_lizard_warning_score_absolute(rate):
    return _calculate_score_absolute(rate, LIZARD_WARNINGS_BEST_FIXED, LIZARD_WARNINGS_WORST_FIXED, case=1)


def calculate_unique_score_absolute(rate):
    return _calculate_score_absolute(rate, UNIQUE_BEST_FIXED, UNIQUE_WORST_FIXED)


def calculate_kwstyle_score_absolute(rate):
    return _calculate_score_absolute(rate, KWSTYLE_BEST_FIXED, KWSTYLE_WORST_FIXED, case=1)


def calculate_infer_score_absolute(rate):
    return _calculate_score_absolute(rate, INFER_BEST_FIXED, INFER_WORST_FIXED, case=1)