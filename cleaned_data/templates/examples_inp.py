example_cpp = "int search(int arr[], int n, int x) {\n    int i = 0;\n    for (i = 0; i < n; i++) {\n        if (arr[i] == x) {\n            return i;\n        }\n    }\n    return -1;\n}\nplease generate ten groups of differentiated valid inputs for the above focal method of cpp language, in the format of [Input_1]\\n[Input_2]\\n...[Input_10]. Finally, use END_OF_CASE to finish your answer."
valid_inputs_cpp = """Input_1:
int arr[] = {1, 2, 3, 4, 5};
int n = 5;
int x = 3;

Input_2:
int arr[] = {10, 20, 30, 40, 50, 60};
int n = 6;
int x = 60;

Input_3:
int arr[] = {100, 200, 300, 400};
int n = 4;
int x = 500;

Input_4:
int arr[] = {0, 0, 0, 0, 0};
int n = 5;
int x = 0;

Input_5:
arr = {2, 4, 6, 8, 10, 12};
n = 6;
x = 1;

Input_6:
int arr[] = {-1, -2, -3, -4, -5, -6, -7};
int n = 7;
int x = -7;

Input_7:
int arr[] = {1};
int n = 1;
int x = 1;

Input_8:
int arr = {5, 5, 5, 5, 5};
int n = 5;
int x = 5;

Input_9:
int arr[] = {0, 10, 20, 30, 40, 50};
int n = 6;
int x = 0;

Input_10:
int arr[] = {-1, -2, -3, -4, -5};
int n = 5;
int x = -3;

END_OF_CASE"""
example_java = """static int minDiff ( int arr [ ] , int n , int k ) {
  int result = Integer . MAX_VALUE ;
  Arrays . sort ( arr ) ;
  for ( int i = 0 ;
  i <= n - k ;
  i ++ ) result = Math . min ( result , arr [ i + k - 1 ] - arr [ i ] ) ;
  return result ;
}
please generate ten groups of differentiated valid inputs for the above focal method of java language, in the format of [Input_1]\\n[Input_2]\\n...[Input_10]. Finally, use END_OF_CASE to finish your answer."""

valid_inputs_java = """Input_1:
int[] arr = {1, 3, 7, 9, 11};
int n = 5;
int k = 3;

Input_2:
int[] arr = {10, 20, 30, 40, 50, 60};
int n = 6;
int k = 4;

Input_3:
int[] arr = {5, 10, 15, 20, 25, 30, 35};
int n = 7;
int k = 2;

Input_4:
int[] arr = {2, 4, 6, 8, 10, 12};
int n = 6;
int k = 6;

Input_5:
int[] arr = {9, 8, 7, 6, 5, 4, 3, 2, 1};
int n = 9;
int k = 5;

Input_6:
int[] arr = {1};
int n = 1;
int k = 1;

Input_7:
int[] arr = {5, 5, 5, 5, 5};
int n = 5;
int k = 3;

Input_8:
int[] arr = {0, 10, 20, 30, 40, 50};
int n = 6;
int k = 4;

Input_9:
int[] arr = {-1, -2, -3, -4, -5};
int n = 5;
int k = 2;

Input_10:
int[] arr = {100, 200, 300, 400};
int n = 4;
int k = 1;

END_OF_CASE"""

example_python = """def minDiff ( arr , n , k ) :
    result = + 2147483647
    arr.sort ( )
    for i in range ( n - k + 1 ) :
        result = int ( min ( result , arr [ i + k - 1 ] - arr [ i ] ) )
    return result
please generate ten groups of differentiated valid inputs for the above focal method of python language, in the format of [Input_1]\\n[Input_2]\\n...[Input_10]. Finally, use END_OF_CASE to finish your answer."""

valid_inputs_python = """Input_1:
arr = [1, 3, 7, 9, 11]
n = 5
k = 3

Input_2:
arr = [10, 20, 30, 40, 50, 60]
n = 6
k = 4

Input_3:
arr = [5, 10, 15, 20, 25, 30, 35]
n = 7
k = 2

Input_4:
arr = [2, 4, 6, 8, 10, 12]
n = 6
k = 6

Input_5:
arr = [9, 8, 7, 6, 5, 4, 3, 2, 1]
n = 9
k = 5

Input_6:
arr = [1]
n = 1
k = 1

Input_7:
arr = [5, 5, 5, 5, 5]
n = 5
k = 3

Input_8:
arr = [0, 10, 20, 30, 40, 50]
n = 6
k = 4

Input_9:
arr = [-1, -2, -3, -4, -5]
n = 5
k = 2

Input_10:
arr = [100, 200, 300, 400]
n = 4
k = 1

END_OF_CASE"""

