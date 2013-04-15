import types, copy

class Symbol:
    name = ''
    symbol = None
    type = None
    isContainer = False
    containerType = None
    isVar = False
    isStatic = False
    staticInitializer = ''
    isGlobal = False
    fileName = ''
    
    def __init__(self, name, symbol, isVar = False, isStatic = False, isGlobal = False):
        self.name = name
        self.symbol = symbol
        self.isVar = isVar
        self.isStatic = isStatic
        self.isGlobal = isGlobal
        
class Scope(Symbol):
    children = []
    prevScope = None
    returnsVoid = True
    superScope = None
    interfacesScope = []
    
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
    currentFile = ''
    
    def __init__(self):
        self.intSymbol = Symbol('int', 'int')
        self.intSymbol.type = 'int'                     

        self.floatSymbol = Symbol('float', 'float')
        self.floatSymbol.type = 'float'
                             
        self.stringSymbol = Symbol('string', 'string')
        self.stringSymbol.type = 'string'                     

        #nativeScope = Scope('native', None)
        #self.symbolsStack.addScope(nativeScope)
        nativeScope = self.symbolsStack

        symScreen = Symbol('Screen', None, False, False, True)
        symScreen.fileName = 'Screen.h'
        nativeScope.addSymbol(symScreen)
        
        nativeScope.addSymbol(Symbol('addsprite', None, False, False, False))
        nativeScope.addSymbol(Symbol('pos', None, False, False, False))
        nativeScope.addSymbol(Symbol('_setevent', None, False, False, False))
        nativeScope.addSymbol(Symbol('append', None, False, False, False))
        nativeScope.addSymbol(Symbol('scale', None, False, False, False))
        nativeScope.addSymbol(Symbol('stop', None, False, False, False))
        nativeScope.addSymbol(Symbol('trace', None, False, False, True))
        nativeScope.addSymbol(Symbol('addaction', None, False, False, False))
        nativeScope.addSymbol(Symbol('repeat', None, False, False, True))
        nativeScope.addSymbol(Symbol('sequence', None, False, False, True))
        nativeScope.addSymbol(Symbol('moveto', None, False, False, True))
        nativeScope.addSymbol(Symbol('scaleto', None, False, False, True))
        nativeScope.addSymbol(Symbol('v_scale', None, False, False, True))
        nativeScope.addSymbol(Symbol('getscene', None, False, False, True))
        nativeScope.addSymbol(Symbol('rand', None, False, False, True))
        nativeScope.addSymbol(Symbol('len', None, False, False, True))
        nativeScope.addSymbol(Symbol('quitgame', None, False, False, True))
        nativeScope.addSymbol(Symbol('str', None, False, False, True))
        nativeScope.addSymbol(Symbol('int', None, False, False, True))
        nativeScope.addSymbol(Symbol('c_addtimer', None, False, False, True))
        nativeScope.addSymbol(Symbol('parsexml', None, False, False, True))
        nativeScope.addSymbol(Symbol('ppy_listachievements', None, False, False, True))
        nativeScope.addSymbol(Symbol('ppy_unlockachievement', None, False, False, True))
        nativeScope.addSymbol(Symbol('dict', None, False, False, True))
        nativeScope.addSymbol(Symbol('json_loads', None, False, False, True))
        nativeScope.addSymbol(Symbol('createsound', None, False, False, True))
        nativeScope.addSymbol(Symbol('createaudio', None, False, False, True))
        nativeScope.addSymbol(Symbol('c_invoke', None, False, False, True))
        nativeScope.addSymbol(Symbol('openUrl', None, False, False, True))
        nativeScope.addSymbol(Symbol('getmodel', None, False, False, True))
        nativeScope.addSymbol(Symbol('ppy_setscore', None, False, False, True))
        nativeScope.addSymbol(Symbol('ppy_query', None, False, False, True))
        nativeScope.addSymbol(Symbol('animate', None, False, False, True))
        nativeScope.addSymbol(Symbol('sprite', None, False, False, True))
        nativeScope.addSymbol(Symbol('http_request', None, False, False, True))
        nativeScope.addSymbol(Symbol('moveby', None, False, False, True))
        nativeScope.addSymbol(Symbol('abs', None, False, False, True))
        nativeScope.addSymbol(Symbol('sin', None, False, False, True))
        nativeScope.addSymbol(Symbol('cos', None, False, False, True))
        nativeScope.addSymbol(Symbol('time', None, False, False, True))
        nativeScope.addSymbol(Symbol('c_addtimer', None, False, False, True))
        nativeScope.addSymbol(Symbol('g_moveto', None, False, False, True))
        nativeScope.addSymbol(Symbol('g_scaleto', None, False, False, True))
        nativeScope.addSymbol(Symbol('spawn', None, False, False, True))
        nativeScope.addSymbol(Symbol('sqrt', None, False, False, True))
        nativeScope.addSymbol(Symbol('screensize', None, False, False, True))
        nativeScope.addSymbol(Symbol('delaytime', None, False, False, True))
        nativeScope.addSymbol(Symbol('float', None, False, False, True))
        nativeScope.addSymbol(Symbol('label', None, False, False, True))
        nativeScope.addSymbol(Symbol('readfile', None, False, False, True))
        nativeScope.addSymbol(Symbol('callMethod', None, False, False, True))
        nativeScope.addSymbol(Symbol('c_opendb', None, False, False, True))
        nativeScope.addSymbol(Symbol('round', None, False, False, True))
        nativeScope.addSymbol(Symbol('ppy_userid', None, False, False, True))
        nativeScope.addSymbol(Symbol('c_res_file', None, False, False, True))
        nativeScope.addSymbol(Symbol('c_file_exist', None, False, False, True))
        nativeScope.addSymbol(Symbol('save', None, False, False, True))
        nativeScope.addSymbol(Symbol('log', None, False, False, True))
        nativeScope.addSymbol(Symbol('start_payment', None, False, False, True))
        nativeScope.addSymbol(Symbol('enable_payments', None, False, False, True))
        nativeScope.addSymbol(Symbol('avatar_url', None, False, False, True))
        nativeScope.addSymbol(Symbol('bind', None, False, False, True))
        nativeScope.addSymbol(Symbol('fabs', None, False, False, True))
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
    
    def checkTypes(self, fileName, prog):
        self.currentFile = fileName;
        
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
            isStatic = False
            if len(node) >= 5:
                for decs in node[4]:
                    if decs == 'static':
                        isStatic = True
                        
            varDefs = node[2]
            for d in varDefs:
                symb = scope.findLocalSymbol(d[1][1])
                if not symb:
                    symb = Symbol(d[1][1], d[1])
                    symb.isVar = True
                    symb.isStatic = isStatic                     
                    scope.addSymbol(symb)

            #print "\tVar: ", symb.name, ":", symb.isStatic
            '''                    
            if scope.superScope:
                for child in scope.superScope.children:
                    if child.isVar:
                        symb = scope.findLocalSymbol(child.name)
                        if not symb:
                            symb = Symbol(child.name, child)
                            symb.isVar = True                     
                            scope.addSymbol(symb)
            '''

        elif node[0] == 'fundef':#['fundef', 'f', ['funsig',], None]
            #print "\tFunction: ", node[1]
            isStatic = False
            if len(node) >= 5:
                for decs in node[4]:
                    if decs == 'static':
                        isStatic = True
            
            if node[1][0:3] == 'set':
                node[1] = '_' + node[1]

            fnScope = scope.findLocalSymbol(node[1])
            if not fnScope:
                fnScope = Scope(node[1], node)
                fnScope.isStatic = isStatic
                scope.addScope(fnScope)
            
                if node[2][1]:
                    for arg in node[2][1]:
                        sym = Symbol(arg[0][1], arg)
                        fnScope.addSymbol(sym)
                        
                if node[3]:
                    for child in node[3]:
                        self.scanNode(child, fnScope)
        elif node[0] == 'clsdef':
            clsScope = scope.findSymbol(node[1])
            if not clsScope:        
                clsScope = Scope(node[1], node)
                clsScope.type = node[1]
                clsScope.isContainer = True
                scope.addScope(clsScope)
            else:
                clsScope.interfacesScope = []
                
            clsScope.fileName = self.currentFile.replace('.as', '.h')

            superName = 'Proxy'
            interfaces = ''
            if node[2]:
                for sup in node[2]:
                    if not sup:
                        continue
                    if sup[0] == 'extends':
                        superName = sup[1][1]
                        superScope = scope.findSymbol(superName)
                        if superScope:
                            clsScope.superScope = superScope
                            #for child in superScope.children:
                            #    clsScope.addSymbol(child)
                    else:
                        for iface in sup[1]:
                            ifaceName = iface[1]
                            interfaces += ifaceName + ','
                            ifaceScope = scope.findSymbol(ifaceName)
                            if ifaceScope:
                                clsScope.interfacesScope.append(ifaceScope)
                                #for child in ifaceScope.children:
                                #    clsScope.addSymbol(child)
                            
            print "Class: ", node[1], "extends", superName , "implements", interfaces 
                
            for child in node[3]:
                self.scanNode(child, clsScope)
                   
        elif node[0] == 'interface':
            clsScope = scope.findSymbol(node[1])
            if not clsScope:        
                clsScope = Scope(node[1], node)
                clsScope.type = node[1]
                clsScope.isContainer = True
                scope.addScope(clsScope)

            print "Interface: ", node[1]
            clsScope.fileName = self.currentFile.replace('.as', '.h')
                
            for child in node[3]:
                self.scanNode(child, clsScope)   
        return
        