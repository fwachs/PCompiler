import aslex
import yacc
# Get the token map
tokens = aslex.tokens

def p_Program_0(p) :
    'Program : Directives'
    p[0] = ['prog',p[1]]
    #for i in p[1]: print i,'\n'

def p_Program_1(p):
    'Program : PackageDefinition Program'
    p[0] = ['prog',[p[1],p[2]]]

def p_PackageDefinition(p):
    'PackageDefinition : PACKAGE PackageName Block'
    p[0] = ['pkg', p[2], p[3]]

def p_PackageName_0(p):
    'PackageName : ID'
    p[0] = p[1]

def p_PackageName_1(p):
    'PackageName : PackageName DOT ID'
    p[0] = p[1]+p[2]+p[3]
    
def p_InterfaceDefinition(p):
    'InterfaceDefinition : INTERFACE ClassName ExtendsList Block'
    p[0] = ['interface', p[2],p[3],p[4],p.lineno(1)]
     
def p_ExtendsList(p):
    '''ExtendsList : 
                 | EXTENDS TypeExpressionList'''  
    if len(p)==1:
       p[0] = None
    else:
       p[0] = p[2]
    
def p_VariableDefinition(p):
    'VariableDefinition : VariableDefinitionKind VariableBindingList'
    p[0] = ['vardef',p[1],p[2],p.lineno(1)]

def p_VariableDefinitionKind(p):
    '''VariableDefinitionKind : VAR
                             | CONST'''
    p[0] = p[1]
    p.set_lineno(0,p.lineno(1))
    
def p_VariableBindingList_0(p):
    'VariableBindingList : VariableBinding'
    p[0] = [p[1]]

def p_VariableBindingList_1(p):
    'VariableBindingList : VariableBindingList COMMA VariableBinding'
    p[0] = p[1] + [p[3]]

def p_VariableBinding(p):
    'VariableBinding : TypedIdentifier VariableInitialisation'
    p[0] = ['varbind', p[1], p[2]]

def p_VariableInitialisation(p):
    '''VariableInitialisation : 
                              | EQUALS VariableInitialiser'''
    if len(p)==1:
        p[0] = None
    else:
        p[0] = p[2]
    
def p_VariableInitialiser(p):
    'VariableInitialiser : AssignmentExpression'
    p[0] = p[1]
    
def p_TypedIdentifier_0(p):
    'TypedIdentifier : ID'
    p[0] = ['typeid', p[1], p.lineno(1)]

def p_TypedIdentifier_1(p):
    'TypedIdentifier : ID COLON TypeExpression'
    p[0] = ['typeid', p[1], p[3]]

def p_FunctionDefinition(p):
    'FunctionDefinition : FUNCTION FunctionName FunctionCommon'    
    p[0] = ['fundef', p[2]] + p[3]

def p_FunctionName(p):
    '''FunctionName : ID'''
    if len(p)==2:
        p[0] = p[1]
    else:
        p[0] = '__'+p[1]+'__'+p[2]

def p_FunctionCommon_0(p):
    'FunctionCommon : FunctionSignature Block'
    p[0] = [p[1], p[2]]

def p_FunctionSignature_0(p):
    'FunctionSignature : LPAREN RPAREN ResultType'
    p[0] = ['funsig', None, p[3], p.lineno(1)]

def p_FunctionSignature_1(p):
    'FunctionSignature : LPAREN Parameters RPAREN ResultType'
    p[0] = ['funsig', p[2], p[4], p.lineno(1)]

def p_Parameters(p):
    '''Parameters :
                  | NonemptyParameters'''
    if len(p) == 1:
        p[0] = None
    else:
        p[0] = p[1]

def p_NonemptyParameters_0(p):
    'NonemptyParameters : Parameter'
    p[0] = [p[1]]

def p_NonemptyParameters_1(p):
    'NonemptyParameters : Parameter COMMA NonemptyParameters'
    p[0] = [p[1]] + p[3]

def p_NonemptyParameters_2(p):
    'NonemptyParameters : RestParameter'
    p[0] = p[1]

def p_Parameter_0(p):
    'Parameter : TypedIdentifier'
    p[0] = [p[1]]
    
def p_Parameter_1(p):
    'Parameter : TypedIdentifier EQUALS AssignmentExpression'
    p[0] = [p[1],p[3]]

def p_RestParameter(p):
    'RestParameter : ELLIPSIS ID'
    p[0] = [[p[1],p[2]]]

def p_ResultType(p):
    '''ResultType :
                  | COLON TypeExpression'''
    if len(p) == 1:
        p[0] = None
    else:
        p[0] = p[2]

def p_ClassDefinition(p):
    'ClassDefinition : CLASS ClassName Inheritance Block'
    p[0] = ['clsdef',p[2],p[3],p[4],p.lineno(1)]

def p_ClassName(p):
    'ClassName : ClassIdentifiers'
    p[0] = p[1]

def p_ClassIdentifiers_0(p):
    'ClassIdentifiers : ID'
    p[0] = p[1]

def p_ClassIdentifiers_1(p):
    'ClassIdentifiers : ClassIdentifiers DOT ID'
    p[0] = p[1]+'.'+p[3]

def p_Inheritance_0(p):
    'Inheritance : '
    p[0] = None

def p_Inheritance_1(p):
    'Inheritance : EXTENDS TypeExpression'
    p[0] = [p[2],None]

def p_Inheritance_2(p):
    'Inheritance : IMPLEMENTS TypeExpressionList'
    p[0] = [None,p[2]]

def p_Inheritance_3(p):
    'Inheritance : EXTENDS TypeExpression IMPLEMENTS TypeExpressionList'
    p[0] = [p[2],p[4]]

def p_TypeExpressionList_0(p):
    'TypeExpressionList : TypeExpression'
    p[0] = [p[1]]

def p_TypeExpressionList_1(p):
    'TypeExpressionList : TypeExpressionList COMMA TypeExpression'
    p[0] = p[1] + [p[3]]
    
def p_Directive_0(p):
    '''Directive : EmptyStatement
                 | Statement
                 | AnnotatableDirective
                 | ImportDirective Semicolon'''
    p[0] = [p[1]]

def p_Directive_1(p):
    'Directive : Attributes AnnotatableDirective'    
    p[0] = [p[2]+[p[1]]]
    

def p_AnnotatableDirective(p):
    '''AnnotatableDirective : VariableDefinition Semicolon
                            | FunctionDefinition
                            | ClassDefinition
                            | InterfaceDefinition'''
    p[0] = p[1]

def p_Directives(p):
    '''Directives :
                  | DirectivesPrefix Directive'''
    if len(p)==1:
        p[0] = None
    else:        
        p[0] = p[1] + p[2]

def p_DirectivesPrefix(p):
    '''DirectivesPrefix :
                        | DirectivesPrefix Directive'''
    if len(p)==1:
        p[0] = []
    else:        
        p[0] = p[1] + p[2]

def p_Attributes(p):
    '''Attributes : Attribute
                  | AttributeCombination'''
    p[0] = p[1]

def p_AttributeCombination(p):
    'AttributeCombination : Attribute Attributes'
    p[0] = p[1] + p[2]

def p_Attribute_0(p):
    '''Attribute : ReservedNamespace'''
    p[0] = [p[1]]

def p_ReservedNamespace(p):
    '''ReservedNamespace : PUBLIC
                         | STATIC
                         | PRIVATE
                         | PROTECTED
                         | OVERRIDE
                         | INTERNAL
                         | EXTERN'''
    p[0] = p[1]

def p_ImportDirective(p):
    '''ImportDirective : IMPORT PackageName DOT TIMES
                       | IMPORT PackageName DOT ID'''
    p[0] = ['imp', p[2]+p[3]+p[4],p.lineno(1)]
    
def p_Statement_0(p):
    '''Statement : SuperStatement Semicolon
                 | IfStatement
                 | SwitchStatement
                 | DoStatement Semicolon
                 | WhileStatement
                 | ForStatement
                 | WithStatement
                 | ContinueStatement Semicolon
                 | BreakStatement Semicolon
                 | ReturnStatement Semicolon
                 | ThrowStatement Semicolon
                 | TryStatement
                 | LabeledStatement
                 | ExpressionStatement Semicolon
                 | Block'''    
    p[0] = p[1]

def p_Substatement(p):
    '''Substatement : EmptyStatement
                    | Statement'''
    p[0] = p[1]
    
def p_EmptyStatement(p):
    'EmptyStatement : SEMI'
    p[0] = ['empty'] 

def p_Semicolon(p):
    '''Semicolon :
                 | SEMI'''

def p_SuperStatement(p):
    'SuperStatement : SUPER Arguments'
    p[0] = ['super',p[2],p.lineno(1)]

def p_IfStatement_0(p):
    'IfStatement : IF ParenListExpression Substatement'
    p[0] = ['if',p[2],p[3], None, p.lineno(1)]

def p_IfStatement_1(p):
    'IfStatement : IF ParenListExpression Substatement ELSE Substatement'
    p[0] = ['if',p[2],p[3],p[5], p.lineno(1)]

def p_SwitchStatement(p):
    'SwitchStatement : SWITCH ParenListExpression LBRACE CaseElements RBRACE'
    p[0] = ['switch', p[2], p[4]]
    print "ERROR: line %d: switch not supported"%(p.lineno(1))

def p_CaseElements_0(p):
    'CaseElements : '
    p[0] = None

def p_CaseElements_1(p):
    'CaseElements : CaseLabel'
    p[0] = [p[1]]

def p_CaseElements_2(p):
    'CaseElements : CaseLabel CaseElementsPrefix CaseElement'
    p[0] = [p[1]] + p[2] + p[3]
    
def p_CaseElementsPrefix(p):
    '''CaseElementsPrefix :
                          | CaseElementsPrefix CaseElement'''
    if len(p) == 1:
        p[0] = []
    else:
        p[0] = p[1]+p[2]
        
def p_CaseElement(p):
    '''CaseElement : Directive
                   | CaseLabel'''
    if p[1][0] == 'case' or p[1][0] == 'default':
        p[0] = [p[1]]
    else:
        p[0] = p[1]

def p_CaseLabel_0(p):
    'CaseLabel : CASE ListExpression COLON' 
    p[0] = ['case',p[2]]    
    
def p_CaseLabel_1(p):
    'CaseLabel : DEFAULT COLON'
    p[0] = ['default']

def p_DoStatement(p):
    'DoStatement : DO Substatement WHILE ParenListExpression'
    p[0] = ['do', p[2], p[4], p.lineno(1)]

def p_WhileStatement(p):
    'WhileStatement : WHILE ParenListExpression Substatement'
    p[0] = ['while', p[2], p[3],p.lineno(1)]

def p_ForStatement_0(p):
    'ForStatement : FOR LPAREN ForInitializer SEMI OptionalExpression SEMI OptionalExpression RPAREN Substatement'
    p[0] = ['for', p[3], p[5], p[7], p[9], p.lineno(1)]

def p_ForInitializer(p):
    '''ForInitializer :
                    | ListExpression
                    | VariableDefinition'''
    if len(p) == 1:
        p[0] = None
    else:      
      p[0] = p[1]

def p_OptionalExpression(p):
    '''OptionalExpression : ListExpression
                          | '''
    if len(p) == 1:
        p[0] = None
    else:
        if len(p[1])==1 and p[1][0][0] in ['assign','call','uexp','uexpop','i','s','id','access','array']:
          p[1][0].append('noret')
        p[0] = p[1]

def p_ContinueStatement(p):
    'ContinueStatement : CONTINUE'
    p[0] = [p[1],p.lineno(1)]

def p_BreakStatement(p):
    'BreakStatement : BREAK'
    p[0] = [p[1],p.lineno(1)]

def p_WithStatement(p):
    'WithStatement : WITH ParenListExpression Substatement'
    p[0] = ['with', p[2], p[3]]

def p_ReturnStatement_0(p):
    'ReturnStatement : RETURN Semicolon'
    p[0] = ['ret',None,p.lineno(1)]

def p_ReturnStatement_1(p):
    'ReturnStatement : RETURN ListExpression'
    p[0] = ['ret',p[2],p.lineno(1)]
    
def p_ThrowStatement(p):
    'ThrowStatement : THROW ListExpression'
    p[0] = ['throw', p[2]]

def p_TryStatement_0(p):
    'TryStatement : TRY Block CatchClauses'
    p[0] = ['try', p[2], p[3]]
    print "ERROR: line %d: try not supported"%(p.lineno(1))

def p_TryStatement_1(p):
    'TryStatement : TRY Block CatchClausesOpt FINALLY Block'
    p[0] = ['try',p[2],p[3],p[5]]
    print "ERROR: line %d: try not supported"%(p.lineno(1))

def p_CatchClausesOpt(p):
    '''CatchClausesOpt :
                       | CatchClauses'''
    if len(p) == 1:
        p[0] = None
    else:
        p[0] = p[1]

def p_CatchClauses_0(p):
    'CatchClauses : CatchClause'
    p[0] = [p[1]]

def p_CatchClauses_1(p):
    'CatchClauses : CatchClauses CatchClause'
    p[0] = p[1] + [p[2]]

def p_CatchClause(p):
    'CatchClause : CATCH LPAREN Parameter RPAREN Block'
    p[0] = [p[3],p[5]] 

def p_LabeledStatement(p):
    'LabeledStatement : ID COLON Substatement'
    p[0] = ['label', p[1], p[3]]
    
def p_ExpressionStatement(p):
    'ExpressionStatement : ListExpression'
    if len(p[1])==1:
        if p[1][0][0] in ['assign','call','uexp','uexpop','i','s','id','access','array']:
            p[1][0].append('noret')
        p[0] = p[1][0]        
    elif len(p[1])>1:
        p[0] = p[1]
    else:
        p[0] = None

def p_Block (p):
    'Block : LBRACE Directives RBRACE'
    p[0] = p[2]
    
def p_UnaryExpression_0 (p):
    'UnaryExpression : PostfixExpression'
    p[0] = p[1]

def p_UnaryExpression_1 (p):
    '''UnaryExpression : PostfixExpression PLUSPLUS 
                       | PostfixExpression MINUSMINUS'''
    p[0] = ['uexpop',p[2],p[1],p.lineno(2)]

def p_UnaryExpression_2 (p):
    '''UnaryExpression :  PLUSPLUS PostfixExpression
                       | MINUSMINUS PostfixExpression
                       | PLUS UnaryExpression
                       | MINUS UnaryExpression
                       | NOT UnaryExpression
                       | LNOT UnaryExpression'''
    p[0] = ['uexp',p[1],p[2], p.lineno(1)]

def p_MultiplicativeExpression_0(p):
    'MultiplicativeExpression : UnaryExpression'
    p[0] = p[1]

def p_MultiplicativeExpression_1(p):
    '''MultiplicativeExpression : MultiplicativeExpression TIMES UnaryExpression
                                | MultiplicativeExpression DIVIDE UnaryExpression
                                | MultiplicativeExpression MOD UnaryExpression'''
    p[0] = ['biexp',p[2], p[1], p[3], p.lineno(2)]

def p_AdditiveExpression_0(p):
    'AdditiveExpression : MultiplicativeExpression'
    p[0] = p[1]

def p_AdditiveExpression_1(p):
    '''AdditiveExpression : AdditiveExpression PLUS MultiplicativeExpression 
                          | AdditiveExpression MINUS MultiplicativeExpression'''
    p[0] = ['biexp',p[2], p[1], p[3], p.lineno(2)] 

def p_ShiftExpression_0(p):
    'ShiftExpression : AdditiveExpression'
    p[0] = p[1]

def p_ShiftExpression_1(p):
    '''ShiftExpression : ShiftExpression LSHIFT AdditiveExpression 
                       | ShiftExpression RSHIFT AdditiveExpression 
                       | ShiftExpression URSHIFT AdditiveExpression'''
    p[0] = ['biexp',p[2], p[1], p[3], p.lineno(2)]

def p_RelationalExpression_0(p):
    'RelationalExpression : ShiftExpression'
    p[0] = p[1]

def p_RelationalExpression_1(p):
    '''RelationalExpression : RelationalExpression LT ShiftExpression 
                            | RelationalExpression GT ShiftExpression 
                            | RelationalExpression LE ShiftExpression 
                            | RelationalExpression GE ShiftExpression
                            | RelationalExpression IN ShiftExpression 
                            | RelationalExpression INSTANCEOF ShiftExpression 
                            | RelationalExpression IS ShiftExpression 
                            | RelationalExpression AS ShiftExpression'''
    p[0] = ['biexp',p[2], p[1], p[3], p.lineno(2)]

def p_EqualityExpression_0(p):
    'EqualityExpression : RelationalExpression'
    p[0] = p[1]

def p_EqualityExpression_1(p):
    '''EqualityExpression : EqualityExpression EQ RelationalExpression 
                          | EqualityExpression NE RelationalExpression 
                          | EqualityExpression EEQ RelationalExpression
                          | EqualityExpression NEE RelationalExpression'''
    p[0] = ['biexp',p[2], p[1], p[3], p.lineno(2)]

def p_BitwiseAndExpression_0(p):
    'BitwiseAndExpression : EqualityExpression'
    p[0] = p[1]
    
def p_BitwiseAndExpression_1(p):
    'BitwiseAndExpression : BitwiseAndExpression AND EqualityExpression'
    p[0] = ['biexp',p[2], p[1], p[3], p.lineno(2)]

def p_BitwiseXorExpression_0(p):
    'BitwiseXorExpression : BitwiseAndExpression'
    p[0] = p[1]

def p_BitwiseXorExpression_1(p):
    'BitwiseXorExpression : BitwiseXorExpression XOR BitwiseAndExpression'
    p[0] = ['biexp',p[2], p[1], p[3], p.lineno(2)]

def p_BitwiseOrExpression_0(p):
    'BitwiseOrExpression : BitwiseXorExpression'
    p[0] = p[1]

def p_BitwiseOrExpression_1(p):
    'BitwiseOrExpression : BitwiseOrExpression OR BitwiseXorExpression'
    p[0] = ['biexp',p[2], p[1], p[3], p.lineno(2)]

def p_LogicalAndExpression_0(p):
    'LogicalAndExpression : BitwiseOrExpression'
    p[0] = p[1]

def p_LogicalAndExpression_1(p):
    'LogicalAndExpression : LogicalAndExpression LAND BitwiseOrExpression'
    p[0] = ['biexp',p[2], p[1], p[3], p.lineno(2)]

def p_LogicalOrExpression_0(p):
    'LogicalOrExpression : LogicalAndExpression'
    p[0] = p[1]

def p_LogicalOrExpression_1(p):
    'LogicalOrExpression : LogicalOrExpression LOR LogicalAndExpression'
    p[0] = ['biexp',p[2], p[1], p[3], p.lineno(2)]

def p_ConditionalExpression_0(p):
    'ConditionalExpression : LogicalOrExpression'
    p[0] = p[1]

def p_ConditionalExpression_1(p):
    'ConditionalExpression : LogicalOrExpression CONDOP AssignmentExpression COLON AssignmentExpression'
    p[0] = ['condexp',p[1],p[3],p[5]]

def p_NonAssignmentExpression_0(p):
    'NonAssignmentExpression : LogicalOrExpression'
    p[0] = p[1]
    
def p_NonAssignmentExpression_1(p):
    'NonAssignmentExpression : LogicalOrExpression CONDOP NonAssignmentExpression COLON NonAssignmentExpression'
    p[0] = ['condnoassign',p[1],p[3],p[5]]

def p_AssignmentExpression_0(p):
    'AssignmentExpression : ConditionalExpression'
    p[0] = p[1]

def p_AssignmentExpression_1(p):
    '''AssignmentExpression : PostfixExpression EQUALS AssignmentExpression 
                            | PostfixExpression CompoundAssignment AssignmentExpression 
                            | PostfixExpression LogicalAssignment AssignmentExpression'''
    p[0] = ['assign', p[2], p[1], p[3], p.lineno(2)]
    
def p_CompoundAssignment(p):
    '''CompoundAssignment : TIMESEQUAL
                          | DIVEQUAL
                          | MODEQUAL
                          | PLUSEQUAL
                          | MINUSEQUAL
                          | LSHIFTEQUAL
                          | RSHIFTEQUAL
                          | URSHIFTEQUAL
                          | ANDEQUAL
                          | XOREQUAL
                          | OREQUAL'''
    p[0] = p[1]
    p.set_lineno(0,p.lineno(1))

def p_LogicalAssignment(p):
    '''LogicalAssignment : LANDEQUAL
                         | LOREQUAL'''
    p[0] = p[1]
    p.set_lineno(0,p.lineno(1))

def p_ListExpression_0(p):
    'ListExpression : AssignmentExpression'
    p[0] = [p[1]]

def p__ListExpression_1(p):
    'ListExpression : ListExpression COMMA AssignmentExpression'
    p[0] = p[1] + [p[3]]

def p_TypeExpression(p):
    'TypeExpression : NonAssignmentExpression'
    p[0] = p[1]

def p_SuperExpression_0(p):
    'SuperExpression : SUPER'
    p[0] = ['super', None, p.lineno(1)]
    
def p_SuperExpression_1(p):
    'SuperExpression : SUPER Arguments'
    p[0] = ['super', p[2], p.lineno(1)]
    
def p_PostfixExpression(p):
    '''PostfixExpression : FullPostfixExpression
                         | ShortNewExpression'''
    p[0] = p[1]

def p_FullNewExpression(p):
    'FullNewExpression : NEW FullNewSubexpression Arguments'
    p[0] = ['new', p[2], p[3] ,p.lineno(3)]

def p_FullNewSubexpression_0(p):
    '''FullNewSubexpression : PrimaryExpression
                            | FullNewExpression'''
    p[0] = p[1]

def p_FullNewSubexpression_1(p):
    '''FullNewSubexpression : FullNewSubexpression PropertyOperator
                            | SuperExpression PropertyOperator'''
    p[0] = ['newdot', p[1], p[2]]

    
def p_FullPostfixExpression_0(p):
    '''FullPostfixExpression : PrimaryExpression
                             | FullNewExpression'''
    p[0] = p[1]

def p_FullPostfixExpression_1(p):
    'FullPostfixExpression : FullPostfixExpression Arguments'
    p[0] = ['call', p[1], p[2],p.lineno(2)]

def p_FullPostfixExpression_2(p):
    '''FullPostfixExpression : FullPostfixExpression PropertyOperator
                            | SuperExpression PropertyOperator'''
    p[0] = ['access', p[1], p[2], p.lineno(2)]                     

def p_ShortNewExpression(p):
    'ShortNewExpression : NEW ShortNewSubexpression'
    p[0] = ['new', p[2],[],p.lineno(1)]

def p_ShortNewSubexpression(p):
    '''ShortNewSubexpression : FullNewSubexpression
                            | ShortNewExpression'''
    p[0] = p[1]

def p_PropertyOperator(p):
    '''PropertyOperator : DOT QualifiedIdentifier
                        | Brackets'''
    if len(p)==3:
        p[0] = ['.',p[2]]
    else:
        p[0] = ['[',p[1]]
    p.set_lineno(0,p.lineno(1))

def p_Brackets(p):
    'Brackets : LBRACKET ListExpression RBRACKET'
    p[0] = p[2]
    p.set_lineno(0,p.lineno(1))
    
def p_Arguments_0(p):
    'Arguments : LPAREN RPAREN'
    p[0] = []
    p.set_lineno(0,p.lineno(1))

def p_Arguments_1(p):
    'Arguments : LPAREN ListExpression RPAREN'
    p[0] = p[2]
    p.set_lineno(0,p.lineno(1))
    
def p_PrimaryExpression_0(p):
    '''PrimaryExpression : NULL
                         | TRUE
                         | FALSE
                         | THIS
                         | INT
                         | UINT
                         | BOOLEAN
                         | NUMBER
                         | STRING
                         | VOID'''    
    p[0] = [p[1],p.lineno(1)]

def p_PrimaryExpression_1(p):
    'PrimaryExpression : FCONST'
    p[0] = ['f',p[1],p.lineno(1)]

def p_PrimaryExpression_2(p):
    '''PrimaryExpression : ICONST
                         | HEX'''
    p[0] = ['i',p[1],p.lineno(1)]

def p_PrimaryExpression_3(p):
    'PrimaryExpression : SCONST'
    p[0] = ['s',p[1],p.lineno(1)]
    
def p_PrimaryExpression_5(p):
    '''PrimaryExpression : QualifiedIdentifier
                        | ArrayInitialiser
                        | ParenListExpression'''             
                        #| ReservedNamespace
    p[0] = p[1]
    
def p_ArrayInitialiser(p):
    'ArrayInitialiser : LBRACKET ElementList RBRACKET'
    p[0] = ['array', p[2], p.lineno(1)]

def p_ElementList_0(p):
    'ElementList : '
    p[0] = []

def p_ElementList_1(p):
    'ElementList : LiteralElement'
    p[0] = [p[1]]

def p_ElementList_2(p):
    'ElementList : COMMA ElementList'
    p[0] = p[2]

def p_ElementList_3(p):
    'ElementList : LiteralElement COMMA ElementList'
    p[0] = [p[1]] + p[3]

def p_LiteralElement(p):
    'LiteralElement : AssignmentExpression'
    p[0] = p[1]

def p_ParenExpression(p):
    'ParenExpression : LPAREN AssignmentExpression RPAREN'
    p[0] = p[2]
    
def p_ParenListExpression_0(p):
    'ParenListExpression : ParenExpression'
    p[0] = [p[1]]

def p_ParenListExpression_1(p):
    'ParenListExpression : LPAREN ListExpression COMMA AssignmentExpression RPAREN'
    p[0] = p[2] + [p[4]]
    
def p_QualifiedIdentifier(p):
    '''QualifiedIdentifier : NonAttributeQualifiedIdentifier'''
    p[0] = p[1]
    
def p_NonAttributeQualifiedIdentifier(p):
    '''NonAttributeQualifiedIdentifier : SimpleQualifiedIdentifier'''
    p[0] = p[1]
    
def p_SimpleQualifiedIdentifier(p):
    '''SimpleQualifiedIdentifier : PropertyIdentifier'''
    p[0] = p[1]        

def p_PropertyIdentifier(p):
    '''PropertyIdentifier : ID'''
    p[0] = ['id',p[1],p.lineno(1)]    

#if __name__=='_main_':    
#parser = yacc.yacc()
#data = open('test1/hex.as').read()    
#parser.parse(data, debug=0)

def parse(data,debug=0):
    parser = yacc.yacc(errorlog=yacc.NullLogger())
    p = parser.parse(data,debug=debug)
    return p
