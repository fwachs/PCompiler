import types, copy

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
        
class TypeInferencer():
    symbolsStack = Scope('global', None)
    passCount = 3
    thisScope = None
    
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
            
            if node[2][1]:
                for arg in node[2][1]:
                    sym = Symbol(arg[0][1], arg)
                    fnScope.addSymbol(sym)
                    
            if node[3]:
                for child in node[3]:
                    self.scanNode(child, fnScope)
        elif node[0] == 'clsdef':        
            clsScope = Scope(node[1], node[1])
            scope.addScope(clsScope)
            for child in node[3]:
                self.scanNode(child, clsScope)   
        return
        