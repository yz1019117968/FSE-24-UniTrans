example_code_cpp = """int maxSum(int arr[], int n){
  int sum = 0;
  sort(arr, arr + n );
  for(int i = 0; i < n / 2; i ++){
    sum -= (2 * arr[i]);
    sum += (2 * arr[n - i - 1]);
  }
  return sum;
}"""
example_test_cases_cpp = ["Inputs:\nint[] arr = {1, 2, 3, 4, 5};\nint n = 5;\nOutputs (int):\n12",
                          "Inputs\nint[] arr = {5, 4, 3, 2, 1};\nint n = 5;\nOutputs (int):\n12",
                          "Inputs\nint[] arr = {5, 1, 3, 2, 4};\nint n = 5;\nOutputs (int):\n12",
                          "Inputs\nint[] arr = {1, 2, 3, 4, 5, 6};\nint n = 6;\nOutputs (int):\n18",
                          "Inputs\nint[] arr = {7, 2, 9, 4, 3};\nint n = 5;\nOutputs (int):\n22",
                          "Inputs\nint[] arr = {1};\nint n = 1;\nOutputs (int):\n0",
                          "Inputs\nint[] arr = {2, 2, 2, 2};\nint n = 4;\nOutputs (int):\n0",
                          "Inputs\nint[] arr = {9, 8, 7, 6, 5, 4, 3, 2, 1};\nint n = 9;\nOutputs (int):\n40",
                          "Inputs\nint[] arr = {4, 2, 6, 1, 5, 3};\nint n = 6;\nOutputs (int):\n18",
                          "Inputs\nint[] arr = {-5, -3, -1, 0, 2};\nint n = 5;\nOutputs (int):\n20"]

example_code_python = """def maxSum(arr, n):
    sum = 0
    arr.sort()
    for i in range(0, int(n / 2)):
        sum -= (2 * arr[i])
        sum += (2 * arr[n - i - 1])
    return sum"""
example_test_cases_python = ["Inputs:\narr = [1, 2, 3, 4, 5]\nn = 5\nOutputs:\n12",
                          "Inputs\narr = [5, 4, 3, 2, 1]\nn = 5\nOutputs:\n12",
                          "Inputs\narr = [5, 1, 3, 2, 4]\nn = 5\nOutputs:\n12",
                          "Inputs\narr = [1, 2, 3, 4, 5, 6]\nn = 6\nOutputs:\n18",
                          "Inputs\narr = [7, 2, 9, 4, 3]\nn = 5\nOutputs:\n22",
                          "Inputs\narr = [1]\nn = 1\nOutputs:\n0",
                          "Inputs\narr = [2, 2, 2, 2]\nn = 4\nOutputs:\n0",
                          "Inputs\narr = [9, 8, 7, 6, 5, 4, 3, 2, 1]\nn = 9\nOutputs:\n40",
                          "Inputs\narr = [4, 2, 6, 1, 5, 3]\nn = 6\nOutputs:\n18",
                          "Inputs\narr = [-5, -3, -1, 0, 2]\nn = 5\nOutputs:\n20"]

example_code_java = """static int maxSum(int arr[], int n){
  int sum = 0 ;
  Arrays.sort(arr);
  for(int i = 0; i < n / 2; i ++){
    sum -= (2 * arr[i]);
    sum += (2 * arr[n - i - 1]);
  }
  return sum ;
}"""

example_test_cases_java = ["Inputs:\nint[] arr = {1, 2, 3, 4, 5};\nint n = 5;\nOutputs (int):\n12",
                          "Inputs\nint[] arr = {5, 4, 3, 2, 1};\nint n = 5;\nOutputs (int):\n12",
                          "Inputs\nint[] arr = {5, 1, 3, 2, 4};\nint n = 5;\nOutputs (int):\n12",
                          "Inputs\nint[] arr = {1, 2, 3, 4, 5, 6};\nint n = 6;\nOutputs (int):\n18",
                          "Inputs\nint[] arr = {7, 2, 9, 4, 3};\nint n = 5;\nOutputs (int):\n22",
                          "Inputs\nint[] arr = {1};\nint n = 1;\nOutputs (int):\n0",
                          "Inputs\nint[] arr = {2, 2, 2, 2};\nint n = 4;\nOutputs (int):\n0",
                          "Inputs\nint[] arr = {9, 8, 7, 6, 5, 4, 3, 2, 1};\nint n = 9;\nOutputs (int):\n40",
                          "Inputs\nint[] arr = {4, 2, 6, 1, 5, 3};\nint n = 6;\nOutputs (int):\n18",
                          "Inputs\nint[] arr = {-5, -3, -1, 0, 2};\nint n = 5;\nOutputs (int):\n20"]
