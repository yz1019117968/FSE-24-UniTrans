import math
import collections
import heapq
import sys
import random
import itertools
from math import sqrt, radians, sin, cos, asin, floor
from collections import defaultdict
import numpy as np
import array
import traceback

# TO_FILL_FUNC

if __name__ == '__main__':
    try:
        # EXP_OUT

        # ACT_OUT

        if isinstance(exp_out, float) or isinstance(act_out, float):
            if abs(exp_out - act_out) < 1e-3:
                print("\nOK\n")
            else:
                print(f"Expected Output:{exp_out}\nActual Output:{act_out}\nExpected output and actual output are not equal!")
        else:
            if exp_out == act_out:
                print("\nOK\n")
            else:
                print(f"Expected Output:{exp_out}\nActual Output:{act_out}\nExpected output and actual output are not equal!")
    except Exception as e:
        print(f"Runtime Error:\n{traceback.format_exc()}")
