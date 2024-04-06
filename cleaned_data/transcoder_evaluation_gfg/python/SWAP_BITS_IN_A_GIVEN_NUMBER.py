# Copyright (c) 2019-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
def f_gold ( x , p1 , p2 , n ) :
    set1 = ( x >> p1 ) & ( ( 1 << n ) - 1 )
    set2 = ( x >> p2 ) & ( ( 1 << n ) - 1 )
    xor = ( set1 ^ set2 )
    xor = ( xor << p1 ) | ( xor << p2 )
    result = x ^ xor
    return result


#TOFILL

if __name__ == '__main__':
    param = [
    (95,1,10,5,),
    (16,2,9,4,),
    (55,3,8,3,),
    (75,4,7,2,),
    (90,5,6,1,),
    (58,6,5,6,),
    (69,7,4,7,),
    (5,8,3,8,),
    (36,9,2,9,),
    (62,10,1,10,)
        ]
    n_success = 0
    for i, parameters_set in enumerate(param):
        if f_filled(*parameters_set) == f_gold(*parameters_set):
            n_success+=1
    print("#Results: %i, %i" % (n_success, len(param)))
