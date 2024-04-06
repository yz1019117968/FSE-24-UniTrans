correct_code_python = """def lexNext ( s , n ) :
    s = list(s)
    for i in range ( n - 1 , - 1 , - 1 ) :
        if s [ i ] != 'z' :
            k = ord ( s [ i ] )
            s [ i ] = chr ( k + 1 )
            return ''.join ( s )
        s [ i ] = 'a'
    return \"\""""
correct_code_java = """
static String lexNext ( String str , int n ) {
  char [ ] s = str . toCharArray ( ) ;
  for ( int i = n - 1 ; i >= 0 ; i -- ) {
    if ( s [ i ] != 'z' ) {
      s [ i ] ++ ;
      return String . valueOf ( s ) ;
    }
    s [ i ] = 'a' ;
  }
  return \"\" ;
}"""

test_cases_java = """
Inputs:
String s = "abc";
int n = 3;
Outputs (String):
\"abd\"
Inputs:
String s = "programming";
int n = 11;
Outputs (String):
\"programminh\"
Inputs:
String s = "language";
int n = 8;
Outputs (String):
\"languagf\""""

incorrect_java_python_code = """def lexNext ( s , n ) :
    s = list(s)
    for i in range ( n - 1 , - 1 , - 1 ) :
        if s [ i ] != 'z' :
            k = int ( s [ i ] )
            s [ i ] = chr ( k + 1 )
            return ''.join ( s )
        s [ i ] = 'a'
    return \"\"
"""
correct_code_cpp = """
string lexNext ( string s, int n ) {
  for ( int i = n - 1;
  i >= 0;
  i -- ) {
    if ( s [ i ] != 'z' ) {
      s [ i ] ++;
      return s;
    }
    s [ i ] = 'a';
  }
  return "";
}"""


java_python_refine_example = """Given java code:
static String lexNext ( String s , int n ) {
  char [ ] str = s . toCharArray ( ) ;
  for ( int i = n - 1 ; i >= 0 ; i -- ) {
    if ( str [ i ] != 'z' ) {
      str [ i ] ++ ;
      return String . valueOf ( str ) ;
    }
    str [ i ] = 'a' ;
  }
  return \"\" ;
}
The following python code was translated from the above java code.
def lexNext ( s , n ) :
    s = list(s)
    for i in range ( n - 1 , - 1 , - 1 ) :
        if s [ i ] != 'z' :
            k = int ( s [ i ] )
            s [ i ] = chr ( k + 1 )
            return ''.join ( s )
        s [ i ] = 'a'
    return \"\"
However, there are some bugs in the python code above as evaluated by the following test cases.
Test Case 0:
Inputs:
s = \"abc\";
n = 3;
Outputs (String):
\"abd\"
Execution Result:
Error Type:Runtime Error
Error Line:k = int ( s [ i ] )
Error Message:ValueError: invalid literal for int() with base 10: 'c'
Test Case 1:
Inputs:
s = \"programming\"
n = 11
Outputs:
\"programminh\"
Execution Result:
Error Type:Runtime Error
Error Line:k = int ( s [ i ] )
Error Message:ValueError: invalid literal for int() with base 10: 'g'
Test Case 2:
Inputs:
s = \"language\"
n = 7
Outputs:
\"languagf\"
Execution Result:
Error Type:Runtime Error
Error Line:k = int ( s [ i ] )
Error Message:UnboundLocalError: invalid literal for int() with base 10: 'e'
Please repair bugs for the above python according to the Execution Result of each Test Case. 
No explanation needed.Use END_OF_CASE to finish your answer.
def lexNext ( s , n ) :
    s = list(s)
    for i in range ( n - 1 , - 1 , - 1 ) :
        if s [ i ] != 'z' :
            k = ord ( s [ i ] )
            s [ i ] = chr ( k + 1 )
            return ''.join ( s )
        s [ i ] = 'a'
    return \"\"
END_OF_CASE"""

java_python_refine_example1 = \
"""Given buggy function:
def lexNext ( s , n ) :
    s = list(s)
    for i in range ( n - 1 , - 1 , - 1 ) :
        if s [ i ] != 'z' :
            k = int ( s [ i ] )
            s [ i ] = chr ( k + 1 )  
            return ''.join ( s )
        s [ i ] = 'a'
    return \"\"
Given execution results: 
Test Case 0:
Inputs:
s = \"abc\";
n = 3;
Outputs (String):
\"abd\"
Execution Result:
Error Type:Runtime Error
Error Line:k = int ( s [ i ] )
Error Message:ValueError: invalid literal for int() with base 10: 'c'
Provide a fix for the buggy function according to the execution results. Use END_OF_CASE to finish your answer:
def lexNext ( s , n ) :
    s = list(s)
    for i in range ( n - 1 , - 1 , - 1 ) :
        if s [ i ] != 'z' :
            k = ord ( s [ i ] )
            s [ i ] = chr ( k + 1 )
            return ''.join ( s )
        s [ i ] = 'a'
    return \"\"
END_OF_CASE
"""

python_refine_example2_1 = \
"""Given buggy python code:
def lexNext ( s , n ) :
    s = list(s)
    for i in range ( n - 1 , - 1 , - 1 ) :
        if s [ i ] != 'z' :
            k = int ( s [ i ] ) #<Buggy Line> 
            s [ i ] = chr ( k + 1 )  
            return ''.join ( s )
        s [ i ] = 'a'
    return \"\"
Given test case: 
Inputs:
s = \"abc\";
n = 3;
Outputs (String):
\"abd\"
Error message: ValueError: invalid literal for int() with base 10: 'c'
Fix the buggy line (marked #<Buggy Line>) in the buggy python code according to the error message. Use END_OF_CASE to finish your answer:
def lexNext ( s , n ) :
    s = list(s)
    for i in range ( n - 1 , - 1 , - 1 ) :
        if s [ i ] != 'z' :
            k = ord ( s [ i ] )
            s [ i ] = chr ( k + 1 )
            return ''.join ( s )
        s [ i ] = 'a'
    return \"\"
END_OF_CASE
"""

python_refine_example2_2 = \
"""Given buggy python code:
def lexNext ( s , n ) :
    s = list(s)
    for i in range ( n - 2 , - 2 , - 2 ) :
        if s [ i ] != 'z' :
            k = ord ( s [ i ] ) 
            s [ i ] = chr ( k + 2 )  
            return ''.join ( s )
        s [ i ] = 'a'
    return \"\"
Given test case: 
Inputs:
s = \"abc\";
n = 3;
Outputs (String):
\"abd\"
Error Message: Expected Output:abd,Actual Output:adc,Expected output and actual output are not equal!
Fix the buggy python code according to the error message. Use END_OF_CASE to finish your answer:
def lexNext ( s , n ) :
    s = list(s)
    for i in range ( n - 1 , - 1 , - 1 ) :
        if s [ i ] != 'z' :
            k = ord ( s [ i ] )
            s [ i ] = chr ( k + 1 )
            return ''.join ( s )
        s [ i ] = 'a'
    return \"\"
END_OF_CASE
"""

java_refine_example2_1 = """Given buggy java code:
static String lexNext ( String str , int n ) {
  char [ ] s = str . toCharArray ( ) ;
  for ( int i = n - 1 ; i >= 0 ; i -- ) {
    if ( s [ i ] != 'z' ) {
      s [ i ] = chr ( ord ( s [ i ] ) + 1 ) ; //<Buggy Line>
      return String . valueOf ( s ) ;
    }
    s [ i ] = 'a' ;
  }
  return \"\" ;
}
Given test case: 
Inputs:
s = \"abc\";
n = 3;
Outputs (String):
\"abd\"
Error message: cannot find symbol
Fix the buggy line (marked //<Buggy Line>) in the buggy java code according to the error message. Use END_OF_CASE to finish your answer:
static String lexNext ( String str , int n ) {
  char [ ] s = str . toCharArray ( ) ;
  for ( int i = n - 1 ; i >= 0 ; i -- ) {
    if ( s [ i ] != 'z' ) {
      s [ i ] ++ ;
      return String . valueOf ( s ) ;
    }
    s [ i ] = 'a' ;
  }
  return \"\" ;
}
END_OF_CASE
"""

java_refine_example2_2 = """Given buggy java code:
static String lexNext ( String str , int n ) {
  char [ ] s = str . toCharArray ( ) ;
  for ( int i = n - 2 ; i >= 0 ; i -- ) {
    if ( s [ i ] != 'z' ) {
      s [ i ] ++ ;
      return String . valueOf ( s ) ;
    }
    s [ i ] = 'a' ;
  }
  return \"\" ;
}
Given test case: 
Inputs:
s = \"abc\";
n = 3;
Outputs (String):
\"abd\"
Error Message: Expected Output:abd,Actual Output:acc,Expected output and actual output are not equal!
Fix the buggy java code according to the error message. Use END_OF_CASE to finish your answer:
static String lexNext ( String str , int n ) {
  char [ ] s = str . toCharArray ( ) ;
  for ( int i = n - 1 ; i >= 0 ; i -- ) {
    if ( s [ i ] != 'z' ) {
      s [ i ] ++ ;
      return String . valueOf ( s ) ;
    }
    s [ i ] = 'a' ;
  }
  return \"\" ;
}
END_OF_CASE
"""

cpp_refine_example2_1 = """Given buggy cpp code:
string lexNext ( string s, int n ) {
  for ( int i = n - 1; i >= 0; i -- ) {
    if ( s [ i ] != 'z' ) {
      s [ i ] = chr ( ord ( s [ i ] ) + 1 ) ; //<Buggy Line>
      return s;
    }
    s [ i ] = 'a';
  }
  return \"\";
}
Given test case: 
Inputs:
s = \"abc\";
n = 3;
Outputs (String):
\"abd\"
Error message: \'ord\' was not declared in this scope
Fix the buggy line (marked //<Buggy Line>) in the buggy cpp code according to the error message. Use END_OF_CASE to finish your answer:
string lexNext ( string s, int n ) {
  for ( int i = n - 1; i >= 0; i -- ) {
    if ( s [ i ] != 'z' ) {
      s [ i ] ++;
      return s;
    }
    s [ i ] = 'a';
  }
  return \"\";
}
END_OF_CASE
"""

cpp_refine_example2_2 = """Given buggy cpp code: 
string lexNext ( string s, int n ) {
  for ( int i = n - 2; i >= 0; i -- ) {
    if ( s [ i ] != 'z' ) {
      s [ i ] ++;
      return s;
    }
    s [ i ] = 'a';
  }
  return \"\";
}
Given test case: 
Inputs:
s = \"abc\";
n = 3;
Outputs (String):
\"abd\"
Error Message: Expected Output:abd,Actual Output:acc,Expected output and actual output are not equal!
Fix the buggy cpp code according to the error message. Use END_OF_CASE to finish your answer:
string lexNext ( string s, int n ) {
  for ( int i = n - 1; i >= 0; i -- ) {
    if ( s [ i ] != 'z' ) {
      s [ i ] ++;
      return s;
    }
    s [ i ] = 'a';
  }
  return \"\";
}
END_OF_CASE
"""
