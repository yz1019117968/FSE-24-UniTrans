import java.util.*;
import java.util.stream.*;
import java.lang.*;
public class EvalCoverage{
public static int nearestSmallerEqFib ( int n ) {
  if ( n == 0 || n == 1 ) return n ;
  int f1 = 0 , f2 = 1 , f3 = 1 ;
  while ( f3 <= n ) {
    f1 = f2 ;
    f2 = f3 ;
    f3 = f1 + f2 ;
  }
  return f2 ;
}

public static void main(String args[]) {
        {
int n = 7;
nearestSmallerEqFib(n);
}

}
}
