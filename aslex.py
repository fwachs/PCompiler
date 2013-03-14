import lex
import os

reserved = (
    'AS', 'BOOLEAN', 'BREAK', 'CASE', 'CATCH', 'CLASS', 'CONST', 'CONTINUE',  'DEFAULT', 'DELETE', 'DO', 'DYNAMIC',
    'EACH', 'ELSE',  'EXTENDS', 'EXTERN', 'FALSE', 'FINAL', 'FINALLY', 'FOR', 'FUNCTION',     
    'IF', 'IMPLEMENTS', 'IMPORT', 'IN', 'INCLUDE', 'INSTANCEOF', 'INT', 'INTERFACE', 'INTERNAL', 'IS', 
    'NAMESPACE', 'NATIVE', 'NEW', 'NULL', 'NUMBER',
    'OVERRIDE', 'PACKAGE', 'PRIVATE', 'PROTECTED', 'PROTOTYPE', 'PUBLIC',
    'RETURN',  'STATIC', 'STRING', 'SUPER', 'SWITCH', 'THIS', 'THROW',  'TRUE', 'TRY', 'TYPEOF', 
    'USE', 'UINT', 'VAR', 'VOID', 'WHILE', 'WITH', 'WEAK'
    )
tokens = reserved + (
    # Literals (identifier, integer constant, float constant, string constant)
    'ID', 'ICONST', 'FCONST', 'SCONST', 'HEX',

    # Operators (+,-,*,/,%,|,&,~,^,<<,>>,>>>, ||, &&, !, <, <=, >, >=, ==, !=, ===, !==)
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'OR', 'AND', 'NOT', 'XOR', 'LSHIFT', 'RSHIFT', 'URSHIFT',
    'LOR', 'LAND', 'LNOT',
    'LT', 'LE', 'GT', 'GE', 'EQ', 'NE', 'EEQ', 'NEE',
    
    # Assignment (=, *=, /=, %=, +=, -=, <<=, >>=, >>>=, &=, ^=, |=, &&=, ||=)
    'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL',
    'LSHIFTEQUAL','RSHIFTEQUAL', 'URSHIFTEQUAL',  'ANDEQUAL', 'XOREQUAL', 'OREQUAL', 'LANDEQUAL', 'LOREQUAL',

    # Increment/decrement (++,--)
    'PLUSPLUS', 'MINUSMINUS',

    # Conditional operator (?)
    'CONDOP',
    
    # Delimeters ( ) [ ] { } , . ; :
    'LPAREN', 'RPAREN',
    'LBRACKET', 'RBRACKET',
    'LBRACE', 'RBRACE',
    'COMMA', 'DOT', 'SEMI', 'COLON',

    # Ellipsis (...)
    'ELLIPSIS',
    )

# Completely ignored characters
t_ignore           = ' \t\x0c\r'

# Newlines
def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

# Comments
def t_onelinecmt(t):
    r'//[^\n]*'    
    #t.lexer.lineno += 1
    
def t_comment(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')
    
# Operators
t_PLUS             = r'\+'
t_MINUS            = r'-'
t_TIMES            = r'\*'
t_DIVIDE           = r'/'
t_MOD              = r'%'
t_OR               = r'\|'
t_AND              = r'&'
t_NOT              = r'~'
t_XOR              = r'\^'
t_LSHIFT           = r'<<'
t_RSHIFT           = r'>>'
t_URSHIFT           = r'>>>'
t_LOR              = r'\|\|'
t_LAND             = r'&&'
t_LNOT             = r'!'
t_LT               = r'<'
t_GT               = r'>'
t_LE               = r'<='
t_GE               = r'>='
t_EQ               = r'=='
t_NE               = r'!='
t_EEQ              = r'==='
t_NEE              = r'!=='

# Assignment operators

t_EQUALS           = r'='
t_TIMESEQUAL       = r'\*='
t_DIVEQUAL         = r'/='
t_MODEQUAL         = r'%='
t_PLUSEQUAL        = r'\+='
t_MINUSEQUAL       = r'-='
t_LSHIFTEQUAL      = r'<<='
t_RSHIFTEQUAL      = r'>>='
t_URSHIFTEQUAL      = r'>>>='
t_ANDEQUAL         = r'&='
t_OREQUAL          = r'\|='
t_XOREQUAL         = r'^='
t_LANDEQUAL        = r'&&='
t_LOREQUAL         = r'\|\|='

# Increment/decrement
t_PLUSPLUS         = r'\+\+'
t_MINUSMINUS       = r'--'

# ?
t_CONDOP           = r'\?'

# Delimeters
t_LPAREN           = r'\('
t_RPAREN           = r'\)'
t_LBRACKET         = r'\['
t_RBRACKET         = r'\]'
t_LBRACE           = r'\{'
t_RBRACE           = r'\}'
t_COMMA            = r','
t_DOT              = r'\.'
t_SEMI             = r';'
t_COLON            = r':'
t_ELLIPSIS         = r'\.\.\.'

# Identifiers and reserved words

reserved_map = { }
for r in reserved:
    reserved_map[r.lower()] = r

def t_ID(t):
    r'[A-Za-z_][\w_]*'
    t.type = reserved_map.get(t.value,"ID")
    return t

def t_HEX(t):
    r'0[x|X][a-fA-F0-9]+'
    try:
        t.value = int(t.value,16)
    except ValueError:
        print("Integer value too large %d", t.value)
        t.value = 0
    return t

# Integer literal
t_ICONST = r'\d+([uU]|[lL]|[uU][lL]|[lL][uU])?'
    
# Floating literal
t_FCONST = r'((\d+)(\.\d+)([e|E](\+|-)?(\d+))? | (\d+)[e|E](\+|-)?(\d+))([lL]|[fF])?'

# String literal
t_SCONST = r'\"([^\\\n]|(\\.))*?\"'

def t_error(t):
    print("Illegal character %s,at %s:%s" % (t.value,t.lineno,t.lexpos))
    t.lexer.skip(1) 
 
lexer = lex.lex(debug=0)
#lexer.input(open('test1/hex.as','r').read())
#while True:
    #tok = lexer.token()
    #if not tok: break      # No more input  
    #print tok
        
if __name__=='_main_':         
    folder = 'test4/'
    outfolder = 'out1/'    
    files = os.listdir(folder)
    for f in files:
      lexer = lex.lex(debug=0)
      lexer.input(open(folder+f,'r').read())
      fout = open(outfolder+f,'w')
      while True:
        tok = lexer.token()
        if not tok: break      # No more input    
        fout.write(str(tok))
        fout.write('\n')

  
