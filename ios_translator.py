import types

class Symbol:
    name = ''
    symbol = None
    type = None
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

class Scope(Symbol):
    children = []
    prevScope = None
    
    def addScope(self, scope):
        scope.prevScope = self
        scope.children = []
        self.children.append(scope)

    def addSymbol(self, symbol):
        self.children.append(symbol)

    def findSymbol(self, name):
        for child in self.children:
            if child.name == name:
                return child
        
        if self.prevScope:
            return self.prevScope.findSymbol(name)
        
class Translator:
    @staticmethod
    def createTranslator(translatorType):
        if translatorType == 'ios':
            return TranslatorIOS()
        
class TranslatorIOS(Translator):
    mFileHandler = None
    hFileHandler = None
    hFileVarDefs = ''
    hFileMethodDefs = ''
    mFileMethodDefs = ''
    mFileMethodBody = ''
    definedIds = []
    className = None
    methodName = None
    tabDepth = -1
    symbolsStack = Scope('global', None)
    
    def dumpTree(self, prog, tab = 0):
        idx = 0        
        for l in prog:
            if isinstance(l, types.ListType):
                print '%s(%d)['%(self.tabString(tab), idx)
                self.dumpTree(l, tab + 1)
                print self.tabString(tab) + ']'
            elif l:
                if isinstance(l, types.IntType):
                    print '%s(%d) %d'%(self.tabString(tab), idx, l)                          
                else:
                    print '%s(%d) %s'%(self.tabString(tab), idx, l)
            else:
                print '%s(%d) None'%(self.tabString(tab), idx)
                    
            idx += 1                          
        return
    
    def checkTypes(self, prog):
        self.scanSymbols(prog[0][1])
        
        self.inferTypes(prog[0][1], self.symbolsStack)
        
        self.dumpTree(prog)
        return
    
    def scanSymbols(self, prog):
        for node in prog:
            self.scanNode(node, self.symbolsStack)
        return
    
    def scanNode(self, node, scope):
        if node[0] == 'vardef':#['vardef', 'const', [['varbind', ['typeid', 'b', ['int']], None]]]        
            varDefs = node[2]
            for d in varDefs:
                symb = Symbol(d[1][1], d[1])                     
                scope.addSymbol(symb)
        elif node[0] == 'fundef':#['fundef', 'f', ['funsig',], None]
            fnScope = Scope(node[1], node)
            scope.addScope(fnScope)
            for child in node[3]:
                self.scanNode(child, fnScope)
        elif node[0] == 'clsdef':        
            clsScope = Scope(node[1], node[1])
            scope.addScope(clsScope)
            for child in node[3]:
                self.scanNode(child, clsScope)   
        return
    
    def inferTypes(self, node, scope):
        if not node:
            return
        
        print node
                
        if node[0] == 'vardef':#['vardef', 'const', [['varbind', ['typeid', 'b', ['int']], None]]]        
            varDefs = node[2]
            for d in varDefs:
                if d[2]:
                    T = self.evalType(d[2], scope)
                    if T:
                        d[1].append(T)
                        sym = scope.findSymbol(d[1][1])
                        sym.type = T
        elif node[0] == 'fundef':#['fundef', 'f', ['funsig',], None]
            #node[2][1] -> function signature
            fnScope = scope.findSymbol(node[1])
            self.inferTypes(node[3], fnScope)
        elif node[0] == 'clsdef':        
            clsScope = scope.findSymbol(node[1])
            self.inferTypes(node[3], clsScope)
        elif node[0] == 'call':#['call', ['id', 'f'], [[],[]]]
            methodSymbol = scope.findSymbol(node[1][1])
            if methodSymbol:
                idx = 0
                for arg in node[2]:
                    T = self.evalType(arg, scope)
                    if T:
                        #methodSymbol[2][1][idx].append(T)
                        idx += 1
            # else:
            # the function symbol has not been defined yet
            # could be a global or class method
            # can cycle through all global functions, classes, class methods & attributes before starting,
            # so no ids would be undefined    
        elif node[0] == 'super':
            pass
        elif node[0] == 'ret':
            T = self.evalType(node[1][0], scope)
            if T:
                scope.type = T
                fnNode = scope.symbol
                fnNode[2][2] = T
        elif node[0] == 'id': #['id', 'a']
            pass
        elif node[0] == 'access':#['access', ['id', 'a'], ['[', [['i', '0']]] ]  #['access', ['this'], ['.', ['id', 'a']]]
            pass
        elif node[0] == 'assign':#['assign', '=', ['id', 'a'], ['biexp', '*', ['id', 'a'], ['i', '2']]]
            T = self.evalType(node[3], scope)
            if T:
                sym = scope.findSymbol(node[2][1])
                node[2].append(T)
                sym.node = node[2]
                sym.type = T
        elif node[0] == 'uexp':
            pass
        elif node[0] == 'uexpop':
            pass
        elif node[0] == 'biexp':#['biexp', '*', ['i', '2'], ['i', '2']]        
            pass
        elif node[0] == 'i':        
            pass
        elif node[0] == 'f':
            pass
        elif node[0] == 's':       
            pass
        elif node[0] == 'array':
            pass
        elif node[0] == 'if':#['if', [['biexp',]], [['vardef', ],], ['if', [['biexp',], [['vardef', ],]],
            #condition
            self.inferTypes(node[1], scope)
            #then
            self.inferTypes(node[2], scope)
            #else
            self.inferTypes(node[3], scope)
        elif node[0] == 'do': 
            pass
        elif node[0] == 'while':        
            pass
        elif node[0] == 'for':
            pass
        elif node[0] == 'continue':
            pass
        elif node[0] == 'break':
            pass
        elif node[0] == 'imp':
            pass
        elif node[0] == 'null':
            pass        
        elif node[0] == 'this':
            pass
        else:
            for n in node:
                self.inferTypes(n, scope)
        return None
    
    def evalType(self, expr, scope):
        if expr[0] == 'i':
            return 'int'
        elif expr[0] == 's':
            return 'string'
        elif expr[0] == 'id':
            idToFind = expr[1]
            sym = scope.findSymbol(idToFind)
            if sym:
                return sym.type
        #elif isinstance(expr[0], types.ListType):
        #    return self.evalType(expr[0])

        return None
    
    def beginFile(self, fileName):
        mFileName = fileName.replace('.as', '.m')
        hFileName = fileName.replace('.as', '.h')
        path = ''
        
        self.mFileHandler = open(path + mFileName, 'w+')
        self.hFileHandler = open(path + hFileName, 'w+')
        return
    
    def endFile(self):
        self.mFileHandler.close()
        self.mFileHandler = None
        
        self.hFileHandler.close()
        self.hFileHandler = None
        return
    
    def beginClass(self, node):
        self.className = node[1]
        
        self.mFileHandler.write('@implementation %s\n\n'%(self.className))
        return
    
    def endClass(self, node):
        self.hFileHandler.write('@interface %s {\n%s}\n\n%s\n@end\n'%(self.className, self.hFileVarDefs, self.hFileMethodDefs))
        self.mFileHandler.write('%s@end\n'%(self.mFileMethodDefs))
        self.className = None
        return
    
    def beginMethod(self, node):        
        signature = node[2][1]
        
        funcString = ''
        if node[1] == 0:
            funcString = '- (id)init'
            self.methodName = 'init'
        else:
            self.methodName = node[1]
        
            funcString = '- (id)%s'%(node[1])
            if signature != None:
                if len(signature):
                    idx = 0
                    for arg in signature:
                        funcString += 'WithArg%d:(id)%s'%(idx, arg[0][1])
                        idx = idx + 1     
                        if idx < len(signature):
                            funcString += ' '
                
                    
        self.hFileMethodDefs += funcString + ';\n'
        
        self.mFileMethodBody += funcString + '\n{\n'           
        return
    
    def emptyRet(self, node):
        self.statementBegin()

        if node[1] == 0:
            self.mFileMethodBody += 'return self'
        else:
            self.mFileMethodBody += 'return Nil'
            
        self.statementEnd()
        return
        
    def endMethod(self, node):
        self.mFileMethodBody += '}\n\n'
        
        self.mFileHandler.write(self.mFileMethodBody)
        self.mFileMethodBody = ''
        
        self.methodName = None           
        
        self.tabDepth = 0
        return
    
    def localId(self, name):
        self.mFileMethodBody += name
        return
    
    def memberId(self, name):
        if name not in self.definedIds:
            self.hFileVarDefs += '\tid %s;\n'%(name)
            self.definedIds.append(name)
        
        self.mFileMethodBody += 'self.%s'%(name)
        return
    
    def staticMemberId(self, name):
        if name not in self.definedIds:
            self.hFileMethodDefs = '+ (id)%s;\n'%(name) + self.hFileMethodDefs
            self.mFileMethodDefs = '+ (id)%s\n{\n\tstatic id _%s;\n\n\treturn _%s;\n}\n\n'%(name, name, name) + self.mFileMethodDefs
            self.definedIds.append(name)
        return
    
    def memberFunctionId(self, name):
        self.mFileMethodBody += 'self %s'%(name)
        return
    
    def staticFunctionId(self, name):
        return
    
    def methodCallBegin(self):
        self.mFileMethodBody += '['
        return
    
    def methodCallArgument(self, argIdx):
        if argIdx > 0:
            self.mFileMethodBody += ' '
        self.mFileMethodBody += 'WithArg%d:'%(argIdx)
        return
    
    def methodCallEnd(self):
        self.mFileMethodBody += ']'
        return
    
    def intConstant(self, intConst):
        self.mFileMethodBody += '%d'%(intConst)
        return
    
    def floatConstant(self, floatConst):
        self.mFileMethodBody += '%f'%(floatConst)
        return
    
    def stringConstant(self, stringConst):
        self.mFileMethodBody += '@' + stringConst
        return

    def nullConstant(self):
        self.mFileMethodBody += 'Nil'
        return
        
    def assignBegin(self):
        return
    
    def assignMiddle(self, operator):
        self.mFileMethodBody += ' %s '%(operator)
        return
    
    def assignEnd(self):
        return
    
    def retBegin(self):
        self.mFileMethodBody += 'return '
        return
    
    def retEnd(self):
        return
    
    def tabString(self, depth):
        tabs = ''
        for i in range(0, depth):
            tabs += '\t'
                    
        return tabs

    def statementBegin(self):
        self.tabDepth += 1
        self.mFileMethodBody += self.tabString(self.tabDepth)
        return
    
    def statementEnd(self):
        self.tabDepth -= 1
        
        if self.methodName:
            self.mFileMethodBody += ';\n'
        return
    
    def ifBegin(self):
        self.mFileMethodBody += 'if'
        return
    
    def ifExpBegin(self):
        self.mFileMethodBody += '('
        return
    
    def ifExpEnd(self):
        self.mFileMethodBody += ') {\n'
        return
    
    def ifElse(self, isSingleStatement):
        if isSingleStatement:
            self.mFileMethodBody += self.tabString(self.tabDepth) + '} else '
        else:
            self.mFileMethodBody += self.tabString(self.tabDepth) + '} else {\n'
        return
    
    def ifEnd(self, isSingleStatement):
        if not isSingleStatement:
            self.mFileMethodBody += self.tabString(self.tabDepth) + '}'
        return
    
    def varDefBegin(self, name, cnt):
        if cnt == 0:
            self.mFileMethodBody += 'id '
        else:
            self.mFileMethodBody += ', '            
            
        self.mFileMethodBody += '%s = '%(name)
        return
    
    def varDefEnd(self):
        return
    
    def binOp(self, operator):
        self.mFileMethodBody += ' %s '%(operator)
        return
    
    def unOp(self, operator):
        self.mFileMethodBody += '%s'%(operator)
        return
    
    def forBegin(self):
        self.mFileMethodBody += 'for('        
        return
    
    def forCondition(self):
        self.mFileMethodBody += '; '        
        return
    
    def forStep(self):
        self.mFileMethodBody += '; '        
        return
    
    def forBlock(self):
        self.mFileMethodBody += ') {\n'        
        return
    
    def forEnd(self):
        self.mFileMethodBody += self.tabString(self.tabDepth) + '}'
        return
    
    def whileBegin(self):
        self.mFileMethodBody += 'while('        
        return
    
    def whileBlock(self):
        self.mFileMethodBody += ') {\n'        
        return
    
    def whileEnd(self):
        self.mFileMethodBody += self.tabString(self.tabDepth) + '}'
        return
    
    def continueStmt(self):
        self.mFileMethodBody += 'continue'
        return
    
    def breakStmt(self):
        self.mFileMethodBody += 'break'
        return
        