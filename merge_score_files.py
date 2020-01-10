#!/usr/bin/env python3
"""
To be used with calculate_score_table.py using the --only-overall-scores flag for easy R^2 computation
"""

import sys

def main():
    file1 = sys.argv[1]
    file2 = sys.argv[2]

    with open(file1) as f1, open(file2) as f2:
        for l1, l2 in zip(f1, f2):
            l1 = l1.replace("\n","")
            l2 = l2.replace("\n","")
            print(l1 + " " + l2)


if __name__ == "__main__":
    main()