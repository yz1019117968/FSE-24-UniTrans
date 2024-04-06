// Copyright (c) 2019-present, Facebook, Inc.
// All rights reserved.
//
// This source code is licensed under the license found in the
// LICENSE file in the root directory of this source tree.
//

import java.util. *;
import java.util.stream.*;
import java.lang.*;
import javafx.util.Pair;
public class SWAP_BITS_IN_A_GIVEN_NUMBER{
static int f_gold ( int x , int p1 , int p2 , int n ) {
  int set1 = ( x >> p1 ) & ( ( 1 << n ) - 1 ) ;
  int set2 = ( x >> p2 ) & ( ( 1 << n ) - 1 ) ;
  int xor = ( set1 ^ set2 ) ;
  xor = ( xor << p1 ) | ( xor << p2 ) ;
  int result = x ^ xor ;
  return result ;
}


//TOFILL

public static void main(String args[]) {
    int n_success = 0;
    List<Integer> param0 = new ArrayList<>();
    param0.add(95);
    param0.add(16);
    param0.add(55);
    param0.add(75);
    param0.add(90);
    param0.add(58);
    param0.add(69);
    param0.add(5);
    param0.add(36);
    param0.add(62);
    List<Integer> param1 = new ArrayList<>();
    param1.add(1);
    param1.add(2);
    param1.add(3);
    param1.add(4);
    param1.add(5);
    param1.add(6);
    param1.add(7);
    param1.add(8);
    param1.add(9);
    param1.add(10);
    List<Integer> param2 = new ArrayList<>();
    param2.add(10);
    param2.add(9);
    param2.add(8);
    param2.add(7);
    param2.add(6);
    param2.add(5);
    param2.add(4);
    param2.add(3);
    param2.add(2);
    param2.add(1);
    List<Integer> param3 = new ArrayList<>();
    param3.add(5);
    param3.add(4);
    param3.add(3);
    param3.add(2);
    param3.add(1);
    param3.add(6);
    param3.add(7);
    param3.add(8);
    param3.add(9);
    param3.add(10);
    for(int i = 0; i < param0.size(); ++i)
    {
        if(f_filled(param0.get(i),param1.get(i),param2.get(i),param3.get(i)) == f_gold(param0.get(i),param1.get(i),param2.get(i),param3.get(i)))
        {
            n_success+=1;
        }
    }
    System.out.println("#Results:" + n_success + ", " + param0.size());
}
}
