import types, copy, type_inference, ios_translator, sys, os
import aslex
import asyacc

class Translator:
    passCount = 0
    maxPasses = 3
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
    
    def begin(self):
        self.inferencer = type_inference.TypeInferencer()        
        
        '''
        errors = 0
        filename = 'prueba.as'
        dirname = 'projects/housewifewars'
        fname = '%s/%s'%(dirname, filename)
        while self.passCount < self.maxPasses:
            print "Pass: ", self.passCount

            if self.passCount == 0:
                print 'Parsing file : %s'%(fname)
                data = open(fname).read()    
                prog = asyacc.parse(data)
                self.programs[fname] = prog
                self.inferencer.checkTypes(self.programs[fname])
            elif self.passCount == 1:
                self.inferencer.checkTypes(self.programs[fname])
            else:
                errors += self.compile(dirname, filename)
            print 'Total errors: ', errors
            self.passCount += 1
        return
        '''
    
    
        while self.passCount < self.maxPasses:
            print "Pass: ", self.passCount
            for dirname, dirnames, filenames in os.walk('projects/test'):
                for filename in filenames:
                    if filename[-3:] == '.as':
                        fname = '%s/%s'%(dirname, filename)
    
                        if self.passCount == 0:
                            data = open(fname).read()    
                            prog = asyacc.parse(data)
                            self.dumpTree(prog)
                            self.programs[fname] = prog
                            self.inferencer.checkTypes(self.programs[fname])
                        elif self.passCount == 1:
                            self.inferencer.checkTypes(self.programs[fname])
                        else:
                            self.compile(dirname, filename)
            self.passCount += 1
            
        self.done()
        
        print "Done!"
        return
    
    def compile(self, dirname, filename):
        fname = '%s/%s'%(dirname, filename)
        
        print '\tTranslating file : %s'%(fname)
            
        errCount = 0
        
        self.currentFileName = fname
        
        prog = self.programs[fname]
        
        self.beginFile(dirname, filename)
    
        self.parseNode(prog[1])

        self.endFile()
            
        try:
            x = 0
        except Exception, err:
            errCount += 1
            print "\t\tError: ", err
        #tyinf.dumpTree(prog)
        
        return errCount
    
    def parseNode(self, node):
        #print "*", self.currentFileName, self.passCount, " -> ", node,'\n'
        
        if not node:
            return
        
        if node[0] == 'vardef':#['vardef', 'const', [['varbind', ['typeid', 'b', ['int']], None]]]
            isStatic = False
            if len(node) >= 5:
                for decs in node[4]:
                    if decs == 'static':
                        isStatic = True
                                            
            cnt = 0
            for n in node[2]:            
                sym = self.inferencer.thisScope.findSymbol(n[1][1])
                if sym:
                    sym.isStatic = isStatic
                
                self.varDefBegin(n[1][1], isStatic, cnt)
                
                if n[2]:
                    T = self.parseNode(n[2])
                else:
                    self.nullConstant()
                                            
                self.varDefEnd(sym)
                cnt += 1
                
        elif node[0] == 'fundef':#['fundef', 'f', ['funsig',], None]
            self.beginMethod(node, False)
    
            if node[3]:
                self.parseNode(node[3])
                
            self.endMethod(node)
            
        elif node[0] == 'clsdef':        
            if node[3]:
                self.inferencer.thisScope = self.inferencer.symbolsStack.findSymbol(node[1])
                
                self.beginClass(node)
                 
                self.parseNode(node[3])
                
                self.endClass(node)                
        elif node[0] == 'new':#['new', ['id', 'f'], [[],[]]]                
            self.newObjectBegin(node[1][1])    
            
            for i in range(len(node[2])):                    
                self.newObjectArgument(i)
                self.parseNode(node[2][i])
                    
            self.newObjectEnd(len(node[2]))
            
        elif node[0] == 'call':#['call', ['id', 'f'], [[],[]]]                
            self.methodCallBegin()
                            
            isGlobal = False
            methodNode = ''
            if node[1][0] == 'access':                    
                self.parseNode(node[1][1])
                methodNode = node[1][2][1]
            else:
                self.this()
                methodNode = node[1]
                if self.inferencer.thisScope:
                    sym = self.inferencer.thisScope.findSymbol(methodNode[1])
                else:
                    sym = self.inferencer.symbolsStack.findSymbol(methodNode[1])                    
                if sym and sym.isGlobal:
                    isGlobal = True

            methodName = methodNode[1]

            self.methodCallBeginArgs(len(node[2]), isGlobal);
                           
            if len(node[2]):
                for i in range(len(node[2])):
                    self.parseNode(node[2][i])
                    self.methodCallArgument(i)
            
            self.methodCallEnd(methodName, isGlobal)
            
        elif node[0] == 'super':
            self.super()

        elif node[0] == 'ret':
            self.retBegin()
            
            if node[1]:
                self.parseNode(node[1][-1])
            
            self.retEnd(node[1])

        elif node[0] == 'id': #['id', 'a']
            idToFind = node[1]
            self.localId(idToFind)
            return idToFind

        elif node[0] == 'access':#['access', ['id', 'a'], ['[', [['i', '0']]] ]  #['access', ['this'], ['.', ['id', 'a']]]
            if node[2][0] == '[':
                self.arrayAccessBegin()
                
                self.parseNode(node[1])
                
                self.arrayAccessMiddle()            
                
                ret = self.parseNode(node[2][1][0])
                
                self.arrayAccessEnd()
                
                return ret
            else:
                self.parseNode(node[1])
                
                self.point()
                
                return self.parseNode(node[2][1])
                
        elif node[0] == 'assign':#['assign', '=', ['id', 'a'], ['biexp', '*', ['id', 'a'], ['i', '2']]]
            assignee = node[2]            
            if assignee[0] == 'access' and assignee[2][0] == '[':
                self.arrayAssignBegin()                        
                self.parseNode(assignee[1])
                self.arrayAssignMiddle(node[1])
                self.parseNode(node[3])
                self.arrayAssignIndex()
                self.parseNode(assignee[2][1][0])
                self.arrayAssignEnd()
            else:
                self.assignBegin()                        
                self.parseNode(node[2])            
                self.assignMiddle()            
                self.parseNode(node[3])
                self.assignEnd(node[1])
            
        elif node[0] == 'uexp':
            self.unOpBegin()
            self.parseNode(node[2])                
            self.unOpEnd(node[1])
        elif node[0] == 'uexpop':
            self.unOpBegin()
            self.parseNode(node[2])                
            self.unOpEnd(node[1])
        elif node[0] == 'biexp':#['biexp', '*', ['i', '2'], ['i', '2']]
            self.binOpBegin()        
            Tto = self.parseNode(node[2])
            self.binOpOperand(node[1])        
            Tfrom = self.parseNode(node[3])
            self.binOpEnd(node[1], Tfrom, Tto)        
            return Tfrom            
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
            self.arrayDefBegin()
            for exp in node[1]:
                self.arrayDefArgBegin()
                self.parseNode(exp)
                self.arrayDefArgEnd()
            self.arrayDefEnd()
                    
        elif node[0] == 'if':#['if', [['biexp',]], [['vardef', ],], ['if', [['biexp',], [['vardef', ],]],
            self.ifBegin()
    
            self.ifExpBegin()
            
            for exp in node[1]:
                self.parseNode(exp)
            
            self.ifExpEnd()
                    
            if node[2]:
                if isinstance(node[2][0], types.ListType):            
                    r1 = self.parseNode(node[2])        
                else:
                    r1 = self.parseNode([node[2]])        
            
            isSingleStatement = False
            if node[3]:
                isSingleStatement = not (isinstance(node[3][0], types.ListType))
                self.ifElse(isSingleStatement)
                
                r2 = self.parseNode(node[3])         
            
            self.ifEnd(isSingleStatement)
                
        elif node[0] == 'do': 
            pass
        
        elif node[0] == 'while':        
            self.whileBegin()
            
            for exp in node[1]:
                self.parseNode(exp)
                
            self.whileBlock()
            if node[2]:
                if isinstance(node[2][0], types.ListType):            
                    r1 = self.parseNode(node[2])        
                else:
                    r1 = self.parseNode([node[2]])        
                
            self.whileEnd()
            
        elif node[0] == 'for':
            self.forBegin()
            
            if node[1]:
                self.parseNode(node[1])
            
            self.forCondition()
            
            if node[2]:
                for exp in node[2]:
                    self.parseNode(exp)
    
            self.forStep()
            
            if node[3]:
                self.parseNode(node[3][0])
            
            self.forBlock()
            
            if node[4]:
                if isinstance(node[4][0], types.ListType):            
                    self.parseNode(node[4])        
                else:
                    self.parseNode([node[4]])        
                
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
                    self.parseNode(n)
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
    
    def super(self):
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

    def arrayDefBegin(self):
        return

    def arrayDefArgBegin(self):
        return
    
    def arrayDefArgEnd(self, argType):
        return

    def arrayDefEnd(self):
        return

if __name__=="__main__":
    trslt = Translator.createTranslator('ios')
    trslt.begin()           
