"""
Functions for calculating the scores for each category that is checked by softwipe.
"""
import math
from scipy.optimize import curve_fit
import numpy as np

def print_score(score, score_name=None):
    """
    Print a score, rounding it to 1 decimal.
    :param score: The score to print.
    :param score_name: Give the score a name which will be printed as well.
    """
    #print(score_name, 'Score: {0:.1f}/10'.format(round(score, 1)))
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
    # This is needed temporarily because of the way the tool folders are walked in the 'calculate_score_table.py'.
    # There can be incomplete reports which would lead to a termination of softwipe.
    #if not rate: return 0;

    # for testing purposes:
    d = best-worst
    #return calculate_score_absolute(rate, best, worst)
    '''steps = 100
    sum_abs = 0
    sum_rel = 0
    sum_err = 0

    mean_abs = 0
    mean_rel = 0

    counter = 0

    range1 = -0.5
    range2 = 1.5

    for i in range(int(range1*steps), int(range2*steps)):
        abs = calculate_score_absolute(i/steps*d + worst, best, worst)
        rel = (10 * i/steps*d) / (best - worst)

        if rel > 10: rel = 10
        elif rel < 0: rel = 0

        mean_abs += abs
        mean_rel += rel

        counter = counter + 1

    mean_abs = mean_abs/counter
    mean_rel = mean_rel/counter

    rel_str = ""
    abs_str = ""

    for i in range(int(range1*steps), int(range2*steps)):
        #print('d: {} - {}'.format(i, i/steps*d))
        #print('i: {}'.format(i))
        abs = calculate_score_absolute(i/steps*d + worst, best, worst)
        rel = (10 * i/steps*d) / (best - worst)

        if rel > 10: rel = 10
        elif rel < 0: rel = 0

        abs_str += str(abs) + " " + str(rel) + "\n"
        rel_str += str(rel) + " " + str(abs) + "\n"

        sum_abs += (abs - mean_rel)**2
        sum_err += (rel - abs)**2
        sum_rel += (rel - mean_rel)**2

        #print(rel)
        #print("abs: {} - rel: {}".format(abs, rel))

    print(abs_str)
    print("----")
    print(rel_str)

    print("------")
    print("r2?: {}".format(1 - sum_err/sum_rel))
    print("------")
    #return calculate_score_absolute(rate, best, worst);'''

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
        #print("score > 10")
        score = 10
    elif score < 0:
        #print("score < 0")
        score = 0

    score_abs = _calculate_score_absolute(rate, best, worst)

    #print("Absolute score: ")
    #print(score_abs)
    #print("Relative score: ")
    #print(score)
    #print("")
    #return score_abs
    return score

'''
The cases cover different possibilities to assemble the evaluation function
case 0: sigmoid  - linear - sigmoid
case 1: sigmoid  - linear - constant
case 2: constant - linear - sigmoid
'''
def _calculate_score_absolute(rate, best, worst, case=0):
    d = best-worst;
    x = (rate - worst)

    if x/d <= 0:
        if case != 2:
            k = (np.log(1/0.01 - 1) - np.log(1/0.05 - 1)) / d
            x0 = np.log(1/0.05 - 1) / k
            return 10 * sigmoid(x, x0, k)
        else:
            return 0
    elif x/d >= 1:
        if case != 1:
            k = (np.log(1/0.95 - 1) - np.log(1/0.99 - 1)) / d
            x0 = np.log(1/0.95 - 1) / k + d
            return 10 * sigmoid(x, x0, k)
        else:
            return 10
    else:
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


    #TODO: Remove the experimental stuff!
    precision = 100
    thresh = 1

    xdata = np.array([0])
    ydata = np.array([thresh/100])
    for i in range(thresh + int(100/precision), 100 - thresh, int(100/precision)):
        xdata = np.append(xdata, i/100*d)
        ydata = np.append(ydata, i/100)
    xdata = np.append(xdata, d)
    ydata = np.append(ydata, 1 - thresh/100)

    #print(xdata)
    #print(ydata)

    #xdata = np.array([0, 0.1*d, 0.2*d, 0.3*d, 0.4*d, 0.5*d, 0.6*d, 0.7*d, 0.8*d, 0.9*d, d])
    #ydata = np.array([0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95])

    #xdata = np.array([0, 0.5*d, d])
    #ydata = np.array([thresh/100, 0.5, 1-thresh/100])

    popt, pcov = curve_fit(sigmoid, xdata, ydata)
    #print(popt)
    ret = sigmoid(rate-worst, *popt)

    return 10*ret;


def sigmoid(x, x0, k):
    #print("x0")
    #print(x0)
    y = 1 / (1 + np.exp(-k * (x - x0)))

    #y = 1 / (1 + np.exp( -k * (-(x - x0) - np.power((x - x0), 3) / 12 )))

    #y = 1 / (1 + np.exp( -k * (-(x - x0) - np.power((x - x0), 3) / 12 - np.power((x - x0), 5) / 80 - np.power((x - x0), 7) / 448)))
    return y


# CONSTANTS TO BE USED BY THE CALCULATION FUNCTIONS

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
INFER_WORST = 0.016       #TODO: recalculate this value!


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
    return _calculate_score_absolute(rate, COMPILER_BEST, COMPILER_WORST, case=1)


def calculate_assertion_score_absolute(rate):
    return _calculate_score_absolute(rate, ASSERTIONS_BEST, ASSERTIONS_WORST, case=2)


def calculate_cppcheck_score_absolute(rate):
    return _calculate_score_absolute(rate, CPPCHECK_BEST, CPPCHECK_WORST)


def calculate_clang_tidy_score_absolute(rate):
    return _calculate_score_absolute(rate, CLANG_TIDY_BEST, CLANG_TIDY_WORST)


def calculate_cyclomatic_complexity_score_absolute(ccn):
    return _calculate_score_absolute(ccn, CYCLOMATIC_COMPLEXITY_BEST, CYCLOMATIC_COMPLEXITY_WORST)


def calculate_lizard_warning_score_absolute(rate):
    return _calculate_score_absolute(rate, LIZARD_WARNINGS_BEST, LIZARD_WARNINGS_WORST, case=1)


def calculate_unique_score_absolute(rate):
    return _calculate_score_absolute(rate, UNIQUE_BEST, UNIQUE_WORST)


def calculate_kwstyle_score_absolute(rate):
    return _calculate_score_absolute(rate, KWSTYLE_BEST, KWSTYLE_WORST, case=1)


def calculate_infer_score_absolute(rate):
    return _calculate_score_absolute(rate, INFER_BEST, INFER_WORST, case=1)