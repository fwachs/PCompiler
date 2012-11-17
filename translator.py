import types, copy, type_inference, ios_translator, sys, os
import aslex
import asyacc

class Translator:
    passCount = 10
    inferencer = None
    programs = {}
    currentFileName = ''
    
    @staticmethod
    def createTranslator(translatorType):
        if translatorType == 'ios':
            return ios_translator.TranslatorIOS()

    def tabString(self, depth):
        tabs = ''
        for i in range(0, depth):
            tabs += '\t'
                    
        return tabs        
    
    def begin(self):
        self.inferencer = type_inference.TypeInferencer()        
        
        '''
        while self.passCount > 0:
            fname = 'projects/housewifewars/prueba.as'
            if self.passCount == 10:
                print 'Parsing file : %s'%(fname)
                data = open(fname).read()    
                prog = asyacc.parse(data)
                self.programs[fname] = prog
                self.inferencer.checkTypes(prog)
            else:
                self.compile(fname)
            self.passCount -= 1
        return
        '''
    
        while self.passCount > 0:
            print "Pass: ", self.passCount
            errors = 0
            for dirname, dirnames, filenames in os.walk('projects/housewifewars'):
                for filename in filenames:
                    if filename[-3:] == '.as':
                        fname = '%s/%s'%(dirname, filename)

                        if self.passCount == 10:
                            print 'Parsing file : %s'%(fname)
                            data = open(fname).read()    
                            prog = asyacc.parse(data)
                            self.programs[fname] = prog
                            self.inferencer.checkTypes(self.programs[fname])
                        elif self.passCount == 9:
                            self.inferencer.checkTypes(self.programs[fname])
                        else:
                            errors += self.compile(fname)
            print 'Total errors: ', errors
            self.passCount -= 1
        return
    
    def compile(self, fname):
        print '\tTranslating file : %s'%(fname)
            
        errCount = 0
        
        self.currentFileName = fname
        
        prog = self.programs[fname]
        
        self.beginFile(fname)
    
        self.parseNode(prog[1], self.inferencer.symbolsStack)

        self.endFile()
            
        try:
            x = 0
        except Exception, err:
            errCount += 1
            print "\t\tError: ", err
        #tyinf.dumpTree(prog)
        
        return errCount
    
    def parseNode(self, node, scope = None):
        print "*", self.currentFileName, self.passCount, " -> ", node,'\n'
        
        if node[0] == 'vardef':#['vardef', 'const', [['varbind', ['typeid', 'b', ['int']], None]]]                                
            cnt = 0
            for n in node[2]:            
                sym = scope.findSymbol(n[1][1])
                if not sym:
                    sym = type_inference.Symbol(n[1][1], n)
                    scope.addSymbol(sym)

                T = sym.type
                self.varDefBegin(n[1][1], T, cnt)
                
                if n[2]:
                    T = self.parseNode(n[2], scope)
                    if T and T.type:
                        n[1].append(T.type)                        
                        sym.type = T.type
                else:
                    self.nullConstant()
                                            
                self.varDefEnd()
                cnt += 1
                
        elif node[0] == 'fundef':#['fundef', 'f', ['funsig',], None]
            fnScope = scope.findSymbol(node[1])
        
            # To prevent Interfaces from failing
            if not fnScope:    
                return None
        
            self.beginMethod(node, fnScope.returnsVoid)
    
            if node[3]:
                self.parseNode(node[3], fnScope)
                
            self.endMethod(node)
            
        elif node[0] == 'clsdef':        
            if node[3]:
                clsScope = scope.findSymbol(node[1])                
                self.beginClass(node)
                self.inferencer.thisScope = clsScope 
                self.parseNode(node[3], clsScope)
                self.endClass(node)
        elif node[0] == 'new':#['new', ['id', 'f'], [[],[]]]                
            self.newObjectBegin(node[1][1])    
            
            constructorSym = None
            clsSym = self.inferencer.symbolsStack.findSymbol(node[1][1])
            if clsSym:
                constructorSym = clsSym.findSymbol(node[1][1])
            for i in range(len(node[2])):                    
                self.newObjectArgument(i)
                Targ = self.parseNode(node[2][i], scope)
                if Targ and constructorSym and constructorSym.symbol[2][1]:
                    signatureArg =  constructorSym.symbol[2][1][i]
                    signatureArg[0].append(Targ)
                    argSym = constructorSym.findSymbol(signatureArg[0][1])
                    #argSym.type = Targ
                    
            self.newObjectEnd()
            
            return clsSym                
            
        elif node[0] == 'call':#['call', ['id', 'f'], [[],[]]]                
            self.methodCallBegin()
                
            methodSymbol = scope.findSymbol(node[1][1])
            
            #print node[1][1]
                
            T = 'None'
            if node[1][0] == 'access':                    
                T = self.parseNode(node[1][1], scope)
                self.space()

                clsScope = scope
                if T:
                    clsScope = self.inferencer.symbolsStack.findSymbol(T.type)
                
                if clsScope:
                    T = self.parseNode(node[1][2][1], clsScope)
                    methodSymbol = clsScope.findSymbol(node[1][2][1][1])             
            else:
                glScope = self.inferencer.symbolsStack.findSymbol("Global")
                T = self.parseNode(node[1], glScope)
               
            if len(node[2]) and methodSymbol and methodSymbol.symbol[2][1]:
                for i in range(len(node[2])):                    
                    self.methodCallArgument(i)
                    Targ = self.parseNode(node[2][i], scope)
                    if Targ and methodSymbol:
                        signatureArg =  methodSymbol.symbol[2][1][i]
                        signatureArg[0].append(Targ)
                        argSym = methodSymbol.findSymbol(signatureArg[0][1])
                        argSym.type = Targ
            
            self.methodCallEnd()
            
            return T
        elif node[0] == 'super':
            return     
        elif node[0] == 'ret':
            self.retBegin()
            
            T = ''
            if node[1]:
                T = self.parseNode(node[1][-1], scope)
            else:
                self.parseNode(['null'], scope)
            
            self.retEnd()
            
            scope.returnsVoid = False
            
            if T and T.type:
                scope.type = T.type
                fnNode = scope.symbol
                fnNode[2][2] = T.type
                return T

        elif node[0] == 'id': #['id', 'a']
            if node[2] == 486 and self.passCount == 7 and self.currentFileName == 'projects/housewifewars/controllers/gift_shop_controller.as':
                x = 0
            idToFind = node[1]
            self.localId(idToFind)
            sym = scope.findSymbol(idToFind)
            if sym:
                return sym

        elif node[0] == 'access':#['access', ['id', 'a'], ['[', [['i', '0']]] ]  #['access', ['this'], ['.', ['id', 'a']]]
            if node[2][0] == '[':
                self.arrayAccessBegin()
                
                T = self.parseNode(node[1], scope)
                
                self.arrayAccessMiddle()            
                
                ret = None
                if T and T.type:
                    clsScope = self.inferencer.symbolsStack.findSymbol(T.type)
                    if clsScope:
                        ret = self.parseNode(node[2][1][0], clsScope)
                
                self.arrayAccessEnd()
                
                return ret
            else:
                T = self.parseNode(node[1], scope)
                
                self.point()
                
                if T and T.type:
                    clsScope = self.inferencer.symbolsStack.findSymbol(T.type)
                    if clsScope:
                        return self.parseNode(node[2][1], clsScope)
                
        elif node[0] == 'assign':#['assign', '=', ['id', 'a'], ['biexp', '*', ['id', 'a'], ['i', '2']]]            
            self.assignBegin()            
            assignee = self.parseNode(node[2], scope)
            
            self.assignMiddle(node[1])
            
            T = self.parseNode(node[3], scope)
            if T and T.type and assignee:
                assignee.symbol.append(T.type)
                assignee.type = T.type
            self.assignEnd()
        elif node[0] == 'uexp':
            if node[1] == '+':
                self.unOp(node[1])
                
                T = self.parseNode(node[2], scope)
                return T
            elif node[1] == '-':
                self.unOp(node[1])
                
                T = self.parseNode(node[2], scope)
                return T
            elif node[1] == '++':
                T = self.parseNode(node[1], scope)
                self.unOp(node[1])
                return T
            elif node[1] == '--':
                T = self.parseNode(node[1], scope)
                self.unOp(node[1])
                return T
            elif node[1] == '~':
                print "Warning: ~ operator not supported"
            elif node[1] == '!':
                self.unOp(node[1])
                
                T = self.parseNode(node[2], scope)
                return T
        elif node[0] == 'uexpop':
            T = self.parseNode(node[2], scope)
            
            self.unOp(node[1])
            return T                        
        elif node[0] == 'biexp':#['biexp', '*', ['i', '2'], ['i', '2']]        
            self.parseNode(node[2], scope)
            self.binOp(node[1])        
            T = self.parseNode(node[3], scope)
            return T            
        elif node[0] == 'i':        
            number = int(node[1])
            self.intConstant(number)
            return self.inferencer.intSymbol
        elif node[0] == 'f':
            number = float(node[1])        
            self.floatConstant(number)
            return self.inferencer.floatSymbol
        elif node[0] == 's':       
            self.stringConstant(node[1])
            return self.inferencer.stringSymbol
        elif node[0] == 'array':
            for exp in node[1]:
                self.parseNode(exp, scope)
            return self.inferencer.symbolsStack.findSymbol('Array')        
        elif node[0] == 'if':#['if', [['biexp',]], [['vardef', ],], ['if', [['biexp',], [['vardef', ],]],
            self.ifBegin()
    
            self.ifExpBegin()
            
            for exp in node[1]:
                self.parseNode(exp, scope)
            
            self.ifExpEnd()
                    
            if node[2]:
                if isinstance(node[2][0], types.ListType):            
                    r1 = self.parseNode(node[2], scope)        
                else:
                    r1 = self.parseNode([node[2]], scope)        
            
            isSingleStatement = False
            if node[3]:
                isSingleStatement = not (isinstance(node[3][0], types.ListType))
                self.ifElse(isSingleStatement)
                
                r2 = self.parseNode(node[3], scope)         
            
            self.ifEnd(isSingleStatement)    
        elif node[0] == 'do': 
            pass
        elif node[0] == 'while':        
            self.whileBegin()
            
            for exp in node[1]:
                self.parseNode(exp, scope)
                
            self.whileBlock()
            if node[2]:
                if isinstance(node[2][0], types.ListType):            
                    r1 = self.parseNode(node[2], scope)        
                else:
                    r1 = self.parseNode([node[2]], scope)        
                
            self.whileEnd()
        elif node[0] == 'for':
            self.forBegin()
            
            if node[1]:
                self.parseNode(node[1], scope)
            
            self.forCondition()
            
            if node[2]:
                for exp in node[2]:
                    self.parseNode(exp, scope)
    
            self.forStep()
            
            if node[3]:
                self.parseNode(node[3][0], scope)
            
            self.forBlock()
            
            if node[4]:
                if isinstance(node[4][0], types.ListType):            
                    r1 = self.parseNode(node[4], scope)        
                else:
                    r1 = self.parseNode([node[4]], scope)        
                
            self.forEnd()
            
        elif node[0] == 'continue':
            self.continueStmt()
        elif node[0] == 'break':
            self.breakStmt()
        elif node[0] == 'imp':
            pass
        elif node[0] == 'null':        
            self.nullConstant()            
        elif node[0] == 'this':
            self.this()
            return self.inferencer.thisScope
        else:
            for n in node:
                if isinstance(n, types.ListType):            
                    self.statementBegin()
                    self.parseNode(n, scope)
                    self.statementEnd()
        return None
    
    def beginFile(self, fileName):
        return
    
    def endFile(self):
        return
    
    def beginClass(self, node):
        return
    
    def endClass(self, node):
        return
    
    def getNativeType(self, type):
        return
    
    def beginMethod(self, node):              
        return
    
    def emptyRet(self, node):
        return
        
    def endMethod(self, node):
        return
    
    def localId(self, name):
        return
    
    def memberId(self, name):
        return
    
    def staticMemberId(self, name):
        return
    
    def memberFunctionId(self, name):
        return
    
    def staticFunctionId(self, name):
        return
    
    def methodCallBegin(self):
        return
    
    def methodCallArgument(self, argIdx):
        return
    
    def methodCallEnd(self):
        return
    
    def newObjectBegin(self, className):
        return
    
    def newObjectArgument(self, argIdx):
        return
    
    def newObjectEnd(self):
        return
    
    def intConstant(self, intConst):
        return
    
    def floatConstant(self, floatConst):
        return
    
    def stringConstant(self, stringConst):
        return

    def nullConstant(self):
        return
        
    def assignBegin(self):
        return
    
    def assignMiddle(self, operator):
        return
    
    def assignEnd(self):
        return
    
    def retBegin(self):
        return
    
    def retEnd(self):
        return
    
    def statementBegin(self):
        return
    
    def statementEnd(self):
        return
    
    def ifBegin(self):
        return
    
    def ifExpBegin(self):
        return
    
    def ifExpEnd(self):
        return
    
    def ifElse(self, isSingleStatement):
        return
    
    def ifEnd(self, isSingleStatement):
        return
    
    def varDefBegin(self, name, type, cnt):
        return
    
    def varDefEnd(self):
        return
    
    def binOp(self, operator):
        return
    
    def unOp(self, operator):
        return
    
    def forBegin(self):
        return
    
    def forCondition(self):
        return
    
    def forStep(self):
        return
    
    def forBlock(self):
        return
    
    def forEnd(self):
        return
    
    def whileBegin(self):
        return
    
    def whileBlock(self):
        return
    
    def whileEnd(self):
        return
    
    def continueStmt(self):
        return
    
    def breakStmt(self):
        return

    def this(self):
        return
    
    def point(self):
        return
    
    def space(self):
        return
    
    def arrayAccessBegin(self):
        return
    
    def arrayAccessMiddle(self):
        return
    
    def arrayAccessEnd(self):
        return

if __name__=="__main__":
    trslt = Translator.createTranslator('ios')
    trslt.begin()           
