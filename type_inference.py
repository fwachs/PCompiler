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
        self.scanSymbols(prog[0][1])
        
        while self.passCount > 0:
            self.inferTypes(prog[0][1], self.symbolsStack)
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
            
            for arg in node[2][1]:
                sym = Symbol(arg[0][1], arg)
                fnScope.addSymbol(sym)
            
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
        if not isinstance(node, types.ListType):
            return
        
        print node
                
        if node[0] == 'vardef':#['vardef', 'const', [['varbind', ['typeid', 'b', ['int']], None]]]        
            varDefs = node[2]
            for d in varDefs:
                sym = scope.findSymbol(d[1][1])
                if not sym:
                    sym = Symbol(d[1][1], d)
                    scope.addSymbol(sym)
                if d[2]:
                    T = self.inferTypes(d[2], scope)
                    if T:
                        if self.passCount == 1:
                            d[1].append(T)                        
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
                    T = self.inferTypes(arg, scope)
                    if T:
                        signatureArg =  methodSymbol.symbol[2][1][idx]
                        if self.passCount == 1:
                            signatureArg[0].append(T)
                        argSym = methodSymbol.findSymbol(signatureArg[0][1])
                        argSym.type = T
                        idx += 1
                return methodSymbol.type
            # else:
            # the function symbol has not been defined yet
            # could be a global or class method
            # can cycle through all global functions, classes, class methods & attributes before starting,
            # so no ids would be undefined    
        elif node[0] == 'super':
            pass
        elif node[0] == 'ret':
            T = self.inferTypes(node[1][0], scope)
            if T:
                scope.type = T
                fnNode = scope.symbol
                if self.passCount == 1:
                    fnNode[2][2] = T
                return T
        elif node[0] == 'id': #['id', 'a']
            idToFind = node[1]
            sym = scope.findSymbol(idToFind)
            if sym:
                return sym.type
        elif node[0] == 'access':#['access', ['id', 'a'], ['[', [['i', '0']]] ]  #['access', ['this'], ['.', ['id', 'a']]]
            pass
        elif node[0] == 'assign':#['assign', '=', ['id', 'a'], ['biexp', '*', ['id', 'a'], ['i', '2']]]
            T = self.inferTypes(node[3], scope)
            if T:
                sym = scope.findSymbol(node[2][1])
                if self.passCount == 1:
                    sym.symbol.append(T)
                sym.type = T
        elif node[0] == 'uexp':
            pass
        elif node[0] == 'uexpop':
            pass
        elif node[0] == 'biexp':#['biexp', '*', ['i', '2'], ['i', '2']]        
            pass
        elif node[0] == 'i':        
            return 'int'
        elif node[0] == 'f':
            pass
        elif node[0] == 's':       
            return 'string'
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
            self.inferTypes(node[1:], scope)
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
        