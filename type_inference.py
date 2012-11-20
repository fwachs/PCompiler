import types, copy

class Symbol:
    name = ''
    symbol = None
    type = None
    isContainer = False
    containerType = None
    isVar = False
    
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol

class Scope(Symbol):
    children = []
    prevScope = None
    returnsVoid = True
    superScope = None
    
    def addScope(self, scope):
        scope.prevScope = self
        scope.children = []
        self.children.append(scope)

    def addSymbol(self, symbol):
        self.children.append(symbol)
        
    def findLocalSymbol(self, name):
        for child in self.children:
            if child.name == name:
                return child
        return

    def findSymbol(self, name):        
        sym = self.findLocalSymbol(name)
        if not sym and self.prevScope:
            sym = self.prevScope.findSymbol(name)
            
        #if not sym and self.superScope:
        #    sym = self.superScope.findSymbol(name)
            
        return sym
        
class TypeInferencer():
    symbolsStack = Scope('global', None)
    passCount = 3
    thisScope = None
    intSymbol = None
    floatSymbol = None
    stringSymbol = None
    
    def __init__(self):
        self.intSymbol = Symbol('int', 'int')
        self.intSymbol.type = 'int'                     

        self.floatSymbol = Symbol('float', 'float')
        self.floatSymbol.type = 'float'
                             
        self.stringSymbol = Symbol('string', 'string')
        self.stringSymbol.type = 'string'                     
        return
    
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
    
    def checkTypes(self, prog):
        self.scanSymbols(prog[1])

        return        
        while self.passCount > 0:
            self.inferTypes(prog[1], self.symbolsStack)
            self.passCount -= 1
        
        self.dumpTree(prog)
        return
    
    def scanSymbols(self, prog):
        if not prog:
            return
        
        for node in prog:
            self.scanNode(node, self.symbolsStack)
        return

    def scanNode(self, node, scope):
        if node[0] == 'vardef':#['vardef', 'const', [['varbind', ['typeid', 'b', ['int']], None]]]        
            varDefs = node[2]
            for d in varDefs:
                symb = scope.findLocalSymbol(d[1][1])
                if not symb:
                    symb = Symbol(d[1][1], d[1])
                    symb.isVar = True                     
                    scope.addSymbol(symb)
                    
            if scope.superScope:
                for child in scope.superScope.children:
                    if child.isVar:
                        symb = scope.findLocalSymbol(child.name)
                        if not symb:
                            symb = Symbol(child.name, child)
                            symb.isVar = True                     
                            scope.addSymbol(symb)

        elif node[0] == 'fundef':#['fundef', 'f', ['funsig',], None]
            print "\tFunction: ", node[1]
            fnScope = scope.findLocalSymbol(node[1])
            if not fnScope:
                fnScope = Scope(node[1], node)
                scope.addScope(fnScope)
            
                if node[2][1]:
                    for arg in node[2][1]:
                        sym = Symbol(arg[0][1], arg)
                        fnScope.addSymbol(sym)
                        
                if node[3]:
                    for child in node[3]:
                        self.scanNode(child, fnScope)
        elif node[0] == 'clsdef':
            if node[1] == 'HUDController':
                x = 0

            clsScope = scope.findSymbol(node[1])
            if not clsScope:        
                clsScope = Scope(node[1], node)
                clsScope.type = node[1]
                clsScope.isContainer = True
                scope.addScope(clsScope)

            superName = ''
            if node[2]:
                if node[2][0]:
                    superScope = scope.findSymbol(node[2][0][1])
                    if superScope:
                        clsScope.superScope = superScope
                        for child in superScope.children:
                            clsScope.addSymbol(child)
                    superName = node[2][0][1]
                #else <interface>

            print "Class: ", node[1], "<", superName , ">"
                
            for child in node[3]:
                self.scanNode(child, clsScope)   
        return
        