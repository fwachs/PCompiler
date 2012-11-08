import types, copy, type_inference, ios_translator, sys, os
import aslex
import asyacc

class Translator:
    translator = None
    
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
        self.compile()
        return
    
    def compile(self):
        fname = 'projects/housewifewars/housewifewars.as'
        
        self.beginFile(fname)
           
        data = open(fname).read()
        currentDir = fname[:fname.rfind(os.sep)+1]
        
        print 'Parsing file : %s'%(fname)
        prog = asyacc.parse(data)
    
        tyinf = type_inference.TypeInferencer()        
        tyinf.checkTypes(prog[1])
        
        self.parseNode(prog[1])
        
        tyinf.dumpTree(prog)
        
        self.endFile()
        return
    
    def parseNode(self, node, loop = False, assign = False):
        print "*    ", node,'\n'
        
        if node[0] == 'vardef':#['vardef', 'const', [['varbind', ['typeid', 'b', ['int']], None]]]                    
            cnt = 0
            for n in node[2]:            
                argType = ''
                if len(n[1]) > 3:
                    argType = n[1][3]
                    
                self.varDefBegin(n[1][1], argType, cnt)

                if n[2]:
                    self.parseNode(n[2])
                else:
                    self.nullConstant()
                                            
                self.varDefEnd()
                cnt += 1
                
        elif node[0] == 'fundef':#['fundef', 'f', ['funsig',], None]
            self.beginMethod(node)
    
            if node[3]:
                self.parseNode(node[3])
            if not node[3] or node[3][-1][0]!='ret':
                self.emptyRet(node)
                
            self.endMethod(node)
            
        elif node[0] == 'clsdef':        
            if node[3]:
                self.beginClass(node)
                self.parseNode(node[3])
                self.endClass(node)
        elif node[0] == 'new':#['new', ['id', 'f'], [[],[]]]
            self.newObjectBegin(node[1][1])    
            
            for i in range(len(node[2])):                    
                self.newObjectArgument(i)
                self.parseNode(node[2][i])
                    
            self.newObjectEnd()                
            
        elif node[0] == 'call':#['call', ['id', 'f'], [[],[]]]
            self.methodCallBegin()    
            sig = self.parseNode(node[1])                
            if sig:
                for i in range(len(sig[1])):                    
                    self.methodCallArgument(i)
                    self.parseNode(node[2][i])
                    
            self.methodCallEnd()
        elif node[0] == 'super':
            return     
        elif node[0] == 'ret':
            self.retBegin()
            
            if node[1]:
                self.parseNode(node[1][-1])
            else:
                self.parseNode(['null'])
            
            self.retEnd()
        elif node[0] == 'id': #['id', 'a']
            self.localId(node[1])

        elif node[0] == 'access':#['access', ['id', 'a'], ['[', [['i', '0']]] ]  #['access', ['this'], ['.', ['id', 'a']]]
            if node[2][0] == '[':
                print 'access ['
                self.parseNode(node[1])            
                self.parseNode(node[2][1][0])
            else:
                if node[1][0] == 'this':                
                    self.memberId(node[2][1][1])
                elif node[1][0] == 'super':
                    print 'access super'
                else:
                    self.parseNode(node[1])            
        elif node[0] == 'assign':#['assign', '=', ['id', 'a'], ['biexp', '*', ['id', 'a'], ['i', '2']]]
            self.assignBegin()
            ret = self.parseNode(node[2],loop,True)
            self.assignMiddle(node[1])
            self.parseNode(node[3])
            self.assignEnd()
        elif node[0] == 'uexp':
            if node[1] == '+':
                self.unOp(node[1])
                
                self.parseNode(node[2])
            elif node[1] == '-':
                self.unOp(node[1])
                
                self.parseNode(node[2])
            elif node[1] == '++':
                self.parseNode(n)
                self.unOp(node[1])            
                return
            elif node[1] == '--':
                self.parseNode(n)
                self.unOp(node[1])
                return
            elif node[1] == '~':
                print "Warning: ~ operator not supported"
            elif node[1] == '!':
                self.unOp(node[1])
                
                self.parseNode(node[2])
        elif node[0] == 'uexpop':
            self.parseNode(node[2])
            
            self.unOp(node[1])                        
        elif node[0] == 'biexp':#['biexp', '*', ['i', '2'], ['i', '2']]        
            self.parseNode(node[2])
            self.binOp(node[1])        
            self.parseNode(node[3])            
        elif node[0] == 'i':        
            number = int(node[1])
            self.intConstant(number)
        elif node[0] == 'f':
            number = float(node[1])        
            self.floatConstant(number)
        elif node[0] == 's':       
            self.stringConstant(node[1])
        elif node[0] == 'array':
            for exp in node[1]:
                self.parseNode(exp)        
        elif node[0] == 'if':#['if', [['biexp',]], [['vardef', ],], ['if', [['biexp',], [['vardef', ],]],
            self.ifBegin()
    
            self.ifExpBegin()
            
            for exp in node[1]:
                self.parseNode(exp)
            
            self.ifExpEnd()
                    
            if node[2]:
                if isinstance(node[2][0], types.ListType):            
                    r1 = self.parseNode(node[2],loop)        
                else:
                    r1 = self.parseNode([node[2]],loop)        
            
            isSingleStatement = False
            if node[3]:
                isSingleStatement = not (isinstance(node[3][0], types.ListType))
                self.ifElse(isSingleStatement)
                
                r2 = self.parseNode(node[3],loop)         
            
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
                    r1 = self.parseNode(node[2],True)        
                else:
                    r1 = self.parseNode([node[2]],True)        
                
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
                    r1 = self.parseNode(node[4],True)        
                else:
                    r1 = self.parseNode([node[4]],True)        
                
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
        else:
            for n in node:
                self.statementBegin()
                self.parseNode(n,loop)
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

if __name__=="__main__":
    trslt = Translator.createTranslator('ios')
    trslt.begin()           
