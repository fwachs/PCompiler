import types

class SymbolsStack:
    symbols = []
    
    def beginScope(self):
        self.symbols.append([])
        return
    
    def endScope(self):
        self.symbols.pop()
        return
    
    def getScope(self, idx):
        return self.symbols[idx]
    
    def addSymbol(self, name, sym):
        scope = self.symbols[-1]
        scope.append([name, sym])            
        return
    
    def findSymbol(self, name, scopeIdx = -1):
        scope = self.symbols[scopeIdx]
            
        for sym in reversed(scope):
            if sym[0] == name:
                return sym[1]
        
        scopeIdx -= 1
        if scopeIdx <= -len(self.symbols):
            return None
        
        return self.findSymbol(name, scopeIdx)

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
    symbolsStack = SymbolsStack()
    
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
        self.symbolsStack.beginScope()
        self.inferTypes(prog[0][1])
        self.symbolsStack.endScope()
        
        self.dumpTree(prog)
        return

    def inferTypes(self, node):
        print node
        
        if not node:
            return
                
        if node[0] == 'vardef':#['vardef', 'const', [['varbind', ['typeid', 'b', ['int']], None]]]        
            varDefs = node[2]
            for d in varDefs:
                if d[2]:
                    T = self.evalType(d[2])
                    if T:
                        d[1].append(T)
                                                    
                self.symbolsStack.addSymbol(d[1][1], d[1])
        elif node[0] == 'fundef':#['fundef', 'f', ['funsig',], None]
            self.symbolsStack.addSymbol(node[1], node)
            self.symbolsStack.beginScope()
            #node[2][1] -> function signature
            self.inferTypes(node[3])
            self.symbolsStack.endScope()
        elif node[0] == 'clsdef':        
            self.symbolsStack.beginScope()
            self.inferTypes(node[3])
        elif node[0] == 'call':#['call', ['id', 'f'], [[],[]]]
            pass
        elif node[0] == 'super':
            pass
        elif node[0] == 'ret':
            T = self.evalType(node[1][0])
            if T:
                scope = self.symbolsStack.getScope(-2)
                fnNode = scope[-1][1]
                fnNode[2][2] = T
        elif node[0] == 'id': #['id', 'a']
            pass
        elif node[0] == 'access':#['access', ['id', 'a'], ['[', [['i', '0']]] ]  #['access', ['this'], ['.', ['id', 'a']]]
            pass
        elif node[0] == 'assign':#['assign', '=', ['id', 'a'], ['biexp', '*', ['id', 'a'], ['i', '2']]]
            T = self.evalType(node[3])
            if T:
                node[2].append(T)
                self.symbolsStack.addSymbol(node[2][1], node[2])
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
            self.inferTypes(node[1])
            #then
            self.inferTypes(node[2])
            #else
            self.inferTypes(node[3])
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
                self.inferTypes(n)
        return None
    
    def evalType(self, expr):
        if expr[0] == 'i':
            return 'int'
        elif expr[0] == 's':
            return 'string'
        elif expr[0] == 'id':
            idToFind = expr[1]
            sym = self.symbolsStack.findSymbol(idToFind)
            if sym and len(sym) > 3:
                return sym[3]
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
        