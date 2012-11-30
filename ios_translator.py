import types, copy, type_inference, translator, os 

class TranslatorIOS(translator.Translator):
    mFileHandler = None
    hFileHandler = None
    hFileVarDefs = ''
    hFilePropDefs = ''
    hFileMethodDefs = ''
    hFileBuff = ''
    mFileMethodDefs = ''
    mFileMethodBody = ''
    mFileBufs = ''
    hFileImports = ''
    tempBodyBuf = []
    definedIds = []
    className = None
    methodName = None
    tabDepth = -1
    isInsideACall = False
    localVars = None
    iVars = None
    refHeaders = []
    constructorCalledSuper = False
    target = ''
    
    def headerExists(self, header):
        for hdr in self.refHeaders:
            if hdr == header:
                return True
        
        return False
        
    def addHeader(self, header):
        if header == '':
            return
        
        if not self.headerExists(header):    
            self.refHeaders.append(header)
            self.mFileHandler.write('#import "%s"\n'%(header))
        return
    
    def addToMethodBody(self, text):
        if len(self.tempBodyBuf) == 0:
            self.mFileMethodBody += text
        else:
            self.tempBodyBuf[-1] += text
        
    def beginMethodBuffering(self):
        self.tempBodyBuf.append('')
        
    def popBuff(self):
        if len(self.tempBodyBuf) > 0:
            return self.tempBodyBuf.pop()
        
    def endMethodBuffering(self):
        if len(self.tempBodyBuf) > 0:
            self.mFileMethodBody += self.tempBodyBuf.pop()
        
    def beginFile(self, dirname, fileName):
        
        path = dirname.replace('projects/' + self.projectName, 'projects/' + self.projectName + '/ios')        
        if not os.path.exists(path):
            os.makedirs(path)
        
        mFileName = fileName.replace('.as', '.m')
        hFileName = fileName.replace('.as', '.h')
        
        self.hFileImports += '#import "%s"\n'%(hFileName)
        
        self.mFileHandler = open('%s/%s'%(path, mFileName), 'w+')
        self.hFileHandler = open('%s/%s'%(path, hFileName), 'w+')
        
        self.hFileHandler.write('#import <Foundation/Foundation.h>\n#import "proxy.h"\n')
        self.mFileHandler.write('#import "%s"\n#import "types.h"\n\n'%(hFileName))
        return
    
    def endFile(self):
        self.mFileHandler.write(self.mFileBufs)
        self.mFileHandler.close()
        self.mFileHandler = None
        self.mFileBufs = ''
        
        self.hFileHandler.write(self.hFileBuff)
        self.hFileHandler.close()
        self.hFileHandler = None
        self.hFileBuff = ''
        self.refHeaders = []
        return
    
    def done(self):
        f = open(self.currentDir + self.projectName + '/ios/defs.h', 'w+')
        f.write(self.hFileImports)
        f.close()

        f = open(self.currentDir + self.projectName + '/ios/CustomProxyProtocol.h', 'w+')
        
        f.write('#import <Foundation/Foundation.h>\n\n')
        f.write('@protocol CustomProxyProtocol <NSObject>\n\n')
                
        definedVars = {}
        definedMethods = {}
        
        for cls in self.inferencer.symbolsStack.children:
            if isinstance(cls, type_inference.Scope):
                for child in cls.children:
                    name = child.name
                    if not child.isStatic and child.isVar:
                        if not definedVars.has_key(name):
                            definedVars[name] = name;
                            f.write('\t@property (strong) Proxy *%s;\n'%(name))
                
        for cls in self.inferencer.symbolsStack.children:
            if isinstance(cls, type_inference.Scope):
                for child in cls.children:
                    name = child.name
                    if name == cls.name:
                        continue
                                                
                    if not definedMethods.has_key(name):
                        definedMethods[name] = name;
                        if not child.isStatic: 
                            if name[0:3] == 'set':
                                f.write('\t- (void)%s:(Proxy *)firstArg, ...;\n'%(name))
                            else:
                                f.write('\t- (Proxy *)%s:(Proxy *)firstArg, ...;\n'%(name))
    
                            if not definedVars.has_key(name):
                                f.write('\t@property (strong) MethodCall %s;\n'%(name))
                        #else:
                            #f.write('\t+ (Proxy*)%s;\n'%(name))
                            #f.write('\t+ (void)set%s:(Proxy *)firstArg, ...;\n'%(name[0:1].title() + name[1:]))
                            

            elif not cls.isGlobal:
                definedMethods[cls.name] = cls.name;
                f.write('\t@property (strong) MethodCall %s;\n'%(cls.name))
                f.write('\t- (Proxy *)%s:(Proxy *)firstArg, ...;\n'%(cls.name))
                
        f.write('\n@end\n')
        
        f.close()
                
        return
    
    def beginClass(self, node):
        self.className = node[1]
        
        self.mFileBufs += '@implementation %s\n\n'%(self.className)
        
        symbol = self.inferencer.symbolsStack.findSymbol(self.className)
        for child in symbol.children:
            name = child.name
                
            if not child.isStatic and name != self.className:
                superSymbol = symbol.superScope;
                if not (superSymbol and superSymbol.findSymbol(name)):
                    self.mFileBufs += '@synthesize %s;\n'%(name)
        self.mFileBufs += '\n'

        superSym = symbol.superScope
        if superSym:
            #if self.headerExists(superSym.fileName):
            self.hFileHandler.write('#import "%s"\n'%(superSym.fileName))

        for iface in symbol.interfacesScope:
            #if self.headerExists(iface.fileName):
            self.hFileHandler.write('#import "%s"\n'%(iface.fileName))

        self.beginMethod([0, 0], False)
        return
    
    def endClass(self, node):
        symbol = self.inferencer.symbolsStack.findSymbol(self.className)
        extends = 'Proxy'
        if symbol.superScope:        
            extends = symbol.superScope.name
        interfaces = ''
        for iface in symbol.interfacesScope:
            if interfaces != '':
                interfaces += ', '
            interfaces += iface.name
        if interfaces != '':
            interfaces = '<' + interfaces + '>'

        self.buildMethodProperties()
        self.buildStaticAccessors()
    
        self.hFileBuff += '@interface %s : %s %s {\n%s}\n\n%s\n\n%s\n@end\n\n'%(self.className, extends, interfaces, self.hFileVarDefs, self.hFilePropDefs, self.hFileMethodDefs)
        self.mFileBufs += '%s\n%s\n@end\n\n'%(self.mFileMethodDefs, self.mFileMethodBody)
        self.className = None
        self.methodName = None
        self.hFileVarDefs = ''
        self.hFilePropDefs = ''
        self.hFileMethodDefs = ''
        self.mFileMethodDefs = ''
        self.mFileMethodBody = ''
        return

    def buildMethodProperties(self):
        self.addToMethodBody('- (void)defineMethods\n{\n\t__weak typeof(self) weakSelf = self;\n\n\t[super defineMethods];\n\n');
        symbol = self.inferencer.symbolsStack.findSymbol(self.className)
        for child in symbol.children:
            if not child.isVar: 
                selfTarget = 'weakSelf'
                if not child.isStatic:
                    name = child.name;
                    if name == self.className:
                        continue
                        
                    self.addToMethodBody('\tself.%s = ^(va_list v_args)\n\t{\n\t\tif(v_args) {\n\t\t\tProxy *firstArg = va_arg(v_args, Proxy *);\n\n\t\t\tProxy *ret = [%s _%s:firstArg args:v_args];\n\t\t\tva_end(v_args);\n\n\t\t\treturn ret;\n\t\t} else {\n\t\t\treturn [%s %s:Nil];\n\t\t}\n\t};\n\n'%(name, selfTarget, name, selfTarget, name))
        self.addToMethodBody('\n}\n\n')
        return
    
    def buildStaticAccessors(self):
        symbol = self.inferencer.symbolsStack.findSymbol(self.className)
        for child in symbol.children:
            if child.isStatic:
                if child.isVar:
                    self.addToMethodBody('static Proxy *_%s;\n\n'%(child.name))
                    self.addToMethodBody('+ (Proxy*)%s\n{\n\t@synchronized(self)\n\t{\n\t\tif(_%s == Nil) {\n\t\t\t_%s = %s;\n\t\t}\n\t}\n\n\treturn _%s;\n}\n\n'%(child.name, child.name, child.name, child.staticInitializer, child.name))
                    self.addToMethodBody('+ (void)set%s:(Proxy*)newValue\n{\n\t_%s = newValue;\n}\n\n'%(child.name[0:1].title() + child.name[1:], child.name))
                    self.hFileMethodDefs += '+ (Proxy*)%s;\n'%(child.name)
                    self.hFileMethodDefs += '+ (void)set%s:(Proxy *)firstArg;\n'%(child.name[0:1].title() + child.name[1:])
                else:
                    self.addToMethodBody('+ (MethodCall)%s\n{\n\tMethodCall m = ^(va_list v_args)\n\t{\n\t\tProxy * firstArg = va_arg(v_args, Proxy *);\n\n\t\tProxy *ret = [%s _%s:firstArg args:v_args];\n\t\tva_end(v_args);\n\n\t\treturn ret;\n\t};\n\n\treturn m;\n}\n\n'%(child.name, self.className, child.name))                    
                    self.hFileMethodDefs += '+ (MethodCall)%s;\n'%(child.name)
        return

    def beginInterface(self, node):
        self.className = node[1]

        self.beginMethodBuffering()        
        return
    
    def endInterface(self, node):
        self.popBuff()
        
        self.hFileBuff += '@protocol %s <NSObject>\n\n%s%s%s\n@end\n\n'%(self.className, self.hFileVarDefs, self.hFilePropDefs, self.hFileMethodDefs)
        self.className = None
        self.methodName = None
        self.hFileVarDefs = ''
        self.hFilePropDefs = ''
        self.hFileMethodDefs = ''
        self.mFileMethodDefs = ''
        self.mFileMethodBody = ''
        return
    
    def getNativeType(self, itype):
        return 'Proxy *'
    
    def beginMethod(self, node, returnsVoid):
        self.constructorCalledSuper = False
        
        if self.methodName == 'init':
            self.endMethod([0, 0])
            constructorSym = self.inferencer.symbolsStack.findSymbol(self.className).findLocalSymbol(self.className)
            if not constructorSym:            
                self.beginMethod([0, self.className, [None, None]], False)
                self.endMethod([0, self.className])            
                        
        funcString = ''
        if not self.className:
            self.methodName = node[1]
            sym = self.inferencer.symbolsStack.findSymbol(self.methodName)
            if not sym:
                print 'Global method not found: %s %s'%(self.methodName, node)
            sym.isGlobal = True
            self.beginMethodBuffering()
            self.addToMethodBody('Proxy *g_%s(Proxy *firstArg, ...)\n{\n\tva_list v_args;\n\tva_start(v_args, firstArg);\n\n'%(self.methodName))
        else :
            if node[1] == 0:
                funcString = '- (void)defineInstanceVars_' + self.className
                self.methodName = 'init'
            else:
                self.methodName = node[1]
            
                methodName = self.methodName 
                if self.methodName == self.className:
                    methodName = 'initWithArgs'
                    
                staticMode = '-'
                if len(node) >= 5:
                    for decoration in node[4]:
                        if decoration == 'static':
                            staticMode = '+'
                            self.inferencer.thisScope.findSymbol(self.methodName).isStatic = True
                            break

                if methodName == 'initWithArgs':
                    funcString = '- (Proxy *)%s:(Proxy *)firstArg args:(va_list)v_args'%(self.classConstructor(self.className))
                    self.hFileMethodDefs += '- (id)initWithArgs:(Proxy *)firstArg, ...;\n'                
                    self.hFileMethodDefs += '- (id)%s:(Proxy *)firstArg args:(va_list)v_args;\n'%(self.classConstructor(self.className))                
                else:                        
                    funcString = '%s (Proxy *)_%s:(Proxy *)firstArg args:(va_list)v_args'%(staticMode, methodName)
                    if staticMode == '-':
                        self.hFileMethodDefs += '@property (strong) MethodCall %s;\n'%(methodName)
                    else:
                        self.hFileMethodDefs += '+ (Proxy*)%s:(Proxy *)firstArg, ...;\n'%(methodName)                
                
            self.addToMethodBody(funcString + '\n{\n')
            
        signature = None
        if node[1] != 0:
            signature = node[2][1]
            
            idx = 0
            if signature != None:                    
                if len(signature):
                    for arg in signature:
                        if idx == 0:
                            self.addToMethodBody('\tProxy *%s = firstArg;\n'%(arg[0][1]))
                        else:
                            self.addToMethodBody('\tProxy *%s = va_arg(v_args, Proxy*);\n'%(arg[0][1]))
                        idx += 1
                self.addToMethodBody('\n')
        
            
        return
    
    def emptyRet(self, node):
        return
    
    def classConstructor(self, className):
        return 'init' + className[0:1].title() + className[1:]
        
    def endMethod(self, node):
        if self.methodName == 'init':
            self.addToMethodBody('')
        elif self.methodName == self.className:
            self.addToMethodBody('\treturn self;\n')
        else:                        
            self.addToMethodBody('\treturn [Proxy nullProxy];\n')
                
        self.addToMethodBody('}\n\n')

        if not self.className:
            self.mFileMethodBody = self.popBuff() + '\n\n' + self.mFileMethodBody
        else:
            if self.methodName != 'init':
                if self.className:
                    staticMode = '-'
                    callTarget = 'self' 
                    sym = self.inferencer.thisScope.findSymbol(self.methodName)
                    if sym and sym.isStatic:
                        staticMode = '+'
                        callTarget = self.className
                        
                    methodName = self.methodName 
                    if self.methodName == self.className:
                        methodName = 'initWithArgs'
                        
                        if not self.constructorCalledSuper:
                            superSym = self.inferencer.thisScope.superScope
                            if superSym:
                                superName = superSym.name
                            else:
                                superName = 'Proxy'
                                
                            self.addToMethodBody('- (id)initWithArgs:(Proxy *)firstArg, ...\n{\n' +
                                             '\tva_list v_args;\n\tva_start(v_args, firstArg);\n' +
                                             '\tself = [super %s:firstArg args:v_args];\n'%(self.classConstructor(superName)) +
                                             '\tva_end(v_args);\n\n' +
                                             '\tva_start(v_args, firstArg);\n' +
                                             '\t[self defineInstanceVars_%s];\n'%(self.className) + 
                                             '\tself = [self %s:firstArg args:v_args];\n'%(self.classConstructor(self.className)) +
                                             '\tva_end(v_args);\n\n\treturn self;\n}\n\n')
                        else:
                            self.addToMethodBody('- (id)initWithArgs:(Proxy *)firstArg, ...\n{\n' +
                                             '\tva_list v_args;\n\tva_start(v_args, firstArg);\n\n' +
                                             '\tself = [self %s:firstArg args:v_args];\n\n'%(self.classConstructor(self.className)) +
                                             '\tva_end(v_args);\n\n\treturn self;\n}\n\n')
                    else:
                        self.addToMethodBody('%s (Proxy *)%s:(Proxy *)firstArg, ...\n{\n\tva_list v_args;\n\tva_start(v_args, firstArg);\n\n\tProxy *ret = [%s _%s:firstArg args:v_args];\n\n\tva_end(v_args);\n\n\treturn ret;\n}\n\n'%(staticMode, methodName, callTarget, methodName))
        
        self.mFileBufs += self.mFileMethodBody
        self.mFileMethodBody = ''
        
        self.methodName = None           
        
        self.tabDepth = 0
        return

    def addSymbolHeader(self, symbolName):    
        symbol = self.inferencer.symbolsStack.findSymbol(symbolName)
        if symbol:
            self.addHeader(symbol.fileName)
            
    def localId(self, name):
        self.addSymbolHeader(name)
        self.addToMethodBody(name)
        return
    
    def memberId(self, name):
        if name not in self.definedIds:
            self.definedIds.append(name)
        
        self.addSymbolHeader(name)
        self.addToMethodBody('self.%s'%(name))
        return
    
    def staticMemberId(self, name):
        self.addSymbolHeader(name)
        if name not in self.definedIds:
            self.hFileMethodDefs = '+ (id)%s;\n'%(name) + self.hFileMethodDefs
            self.mFileMethodDefs = '+ (id)%s\n{\n\tstatic id _%s;\n\n\treturn _%s;\n}\n\n'%(name, name, name) + self.mFileMethodDefs
            self.definedIds.append(name)
        return
    
    def memberFunctionId(self, name):
        self.addSymbolHeader(name)
        self.addToMethodBody('self %s'%(name))
        return
    
    def staticFunctionId(self, name):
        return
    
    def methodCallBegin(self):
        self.isInsideACall = True
        self.beginMethodBuffering()
        return
    
    def methodCallBeginArgs(self, argCnt, isGlobal):
        if isGlobal:
            self.popBuff()
        else:
            self.target = self.popBuff();
            if self.target == 'super' and self.methodName == self.className:
                self.constructorCalledSuper = True
                self.addToMethodBody('self = [super')
            else:
                self.addToMethodBody('[' + self.target)
        self.beginMethodBuffering()
        return
        
    def methodCallArgument(self, argIdx):
        self.isInsideACall = False
        self.addToMethodBody(', ')
        return
    
    def methodCallEnd(self, name, isGlobal):
        self.isInsideACall = False
        if name[0:3] == 'set':
            name = '_' + name
            
        if isGlobal:
            self.addToMethodBody('g_%s(%sNil)'%(name, self.popBuff()))
        else:
            self.addToMethodBody(' %s:%sNil]'%(name, self.popBuff()))

        if self.target == 'super' and self.methodName == self.className:
            self.addToMethodBody(';\n\t[self defineInstanceVars_%s]'%(self.className)) 
        return
    
    def newObjectBegin(self, className):
        self.addSymbolHeader(className)
        
        if className == 'dict':
            className = 'Dict'
        self.addToMethodBody('[[%s alloc] initWithArgs:'%(className))
        return
        
    def newObjectArgument(self, argIdx):
        if argIdx > 0:
            self.addToMethodBody(', ')
        return
    
    def newObjectEnd(self, argsCount):
        if argsCount > 0:
            self.addToMethodBody(', ')
        self.addToMethodBody('Nil]')
        return
    
    def intConstant(self, intConst):
        self.addToMethodBody('[Proxy proxyWithInt:%d]'%(intConst))
        return
    
    def floatConstant(self, floatConst):
        self.addToMethodBody('[Proxy proxyWithFloat:%f]'%(floatConst))
        return
    
    def stringConstant(self, stringConst):
        self.addToMethodBody('[Proxy proxyWithString:@%s]'%(stringConst))
        return

    def nullConstant(self):
        self.addToMethodBody('Nil')
        return
        
    def assignBegin(self):
        self.beginMethodBuffering()            
        return
    
    def assignMiddle(self):
        self.beginMethodBuffering()
        return
    
    def assignEnd(self, operator):
        rightSide = self.popBuff()
        leftSide = self.popBuff()
        
        if operator == '+=':
            self.addToMethodBody('[%s add:%s]'%(leftSide, rightSide))
        elif operator == '-=':
            self.addToMethodBody('[%s sub:%s]'%(leftSide, rightSide))
        else:
            self.addToMethodBody('%s %s %s'%(leftSide, operator, rightSide))
        return

    def arrayAssignBegin(self):
        self.addToMethodBody('[')
        return
                            
    def arrayAssignMiddle(self, operand):
        self.addToMethodBody(' setProxy:')
        return
    
    def arrayAssignIndex(self):
        self.addToMethodBody(' atIndex:')
        return
    
    def arrayAssignEnd(self):
        self.addToMethodBody(']')
        return
    
    def retBegin(self):
        self.addToMethodBody('return ')
        return
    
    def retEnd(self, node):
        if not node:
            self.addToMethodBody('[Proxy nullProxy]')
        return
    
    def statementBegin(self):
        self.tabDepth += 1
        self.addToMethodBody(self.tabString(self.tabDepth))
        return
    
    def statementEnd(self):
        self.tabDepth -= 1
        
        if self.methodName:
            self.addToMethodBody(';\n')
        return
    
    def ifBegin(self):
        self.addToMethodBody('if')
        return
    
    def ifExpBegin(self):
        self.addToMethodBody('([')
        return
    
    def ifExpEnd(self):
        self.addToMethodBody(' intValue]) {\n')
        return
    
    def ifElse(self, isSingleStatement):
        if isSingleStatement:
            self.addToMethodBody(self.tabString(self.tabDepth) + '} else ')
        else:
            self.addToMethodBody(self.tabString(self.tabDepth) + '} else {\n')
        return
    
    def ifEnd(self, isSingleStatement):
        if not isSingleStatement:
            self.addToMethodBody(self.tabString(self.tabDepth) + '}')
        return
    
    def varDefBegin(self, name, isStatic, cnt):                        
        if self.methodName == 'init':
            if isStatic:
                self.beginMethodBuffering()
            else:
                self.hFileVarDefs += '\t%s %s;\n'%(self.getNativeType(None), name)
                self.hFilePropDefs += '@property (strong) Proxy *%s;\n'%(name)
    
                self.addToMethodBody('\t\tself.%s = '%(name))
        else:
            if cnt == 0:
                if isStatic:
                    self.addToMethodBody('static %s '%(self.getNativeType(None)))
                else:
                    self.addToMethodBody('%s '%(self.getNativeType(None)))
            else:
                self.addToMethodBody(', *')
                
            self.addToMethodBody('%s = '%(name))
        return
    
    def varDefEnd(self, symbol):
        if symbol and symbol.isStatic:
            stinit = self.popBuff();
            if not stinit:
                stinit = 'Nil'
            symbol.staticInitializer = stinit
        return
    
    def binOpBegin(self):
        self.beginMethodBuffering()
        return
    
    def binOpOperand(self, operator):
        self.beginMethodBuffering()
        return
    
    def binOpEnd(self, operator, fromType, toType):
        
        rightSide = self.popBuff()
        leftSide = self.popBuff()
            
        methodName = ''    
        if operator == '+':
            methodName = 'add'
        elif operator == '-':
            methodName = 'sub'
        elif operator == '*':
            methodName = 'mul'
        elif operator == '/':
            methodName = 'div'
        elif operator == '%':
            methodName = 'reminder'
        elif operator == '==':
            methodName = 'isEq'
        elif operator == '!=':
            methodName = 'isNotEq'
        elif operator == '>':
            methodName = 'isGt'
        elif operator == '>=':
            methodName = 'isGtOrEq'
        elif operator == '<':
            methodName = 'isLe'
        elif operator == '<=':
            methodName = 'isLeOrEq'
        elif operator == '|':
            methodName = 'bitwiseOr'
        elif operator == '&':
            methodName = 'bitwiseAnd'
        elif operator == '||':
            methodName = 'logicalOr'
        elif operator == '&&':
            methodName = 'logicalAnd'
            
        self.addToMethodBody('[%s %s:%s]'%(leftSide, methodName, rightSide))
        return
    
    def unOpBegin(self):
        self.addToMethodBody('[')
    
    def unOpEnd(self, operator):
        methodName = ''
        if operator == '-':
            methodName = 'neg'
        elif operator == '+':
            methodName = 'plus'
        elif operator == '--':
            methodName = 'dec'
        if operator == '++':
            methodName = 'inc'
        if operator == '!':
            methodName = 'not'
            
        self.addToMethodBody(' %s]'%(methodName))
        return
    
    def forBegin(self):
        self.addToMethodBody('for(')
        return
    
    def forCondition(self):
        self.addToMethodBody('; [')
        return
    
    def forStep(self):
        self.addToMethodBody(' intValue]; ')
        return
    
    def forBlock(self):
        self.addToMethodBody(') {\n')
        return
    
    def forEnd(self):
        self.addToMethodBody(self.tabString(self.tabDepth) + '}')
        return
    
    def whileBegin(self):
        self.addToMethodBody('while([')
        return
    
    def whileBlock(self):
        self.addToMethodBody(' intValue]) {\n')
        return
    
    def whileEnd(self):
        self.addToMethodBody(self.tabString(self.tabDepth) + '}')
        return
    
    def continueStmt(self):
        self.addToMethodBody('continue')
        return
    
    def breakStmt(self):
        self.addToMethodBody('break')
        return

    def this(self):
        self.addToMethodBody('self')
        return

    def super(self):
        self.addToMethodBody('super')
        return

    def point(self):
        self.addToMethodBody('.')
        return

    def space(self):
        self.addToMethodBody(' ')
        return
    
    def arrayAccessBegin(self):
        self.addToMethodBody('[')
        return
    
    def arrayAccessMiddle(self):
        self.addToMethodBody(' proxyAtIndex:')
        return
    
    def arrayAccessEnd(self):
        self.addToMethodBody(']')
        return
    
    def arrayDefBegin(self):
        self.addToMethodBody('[[Array alloc] initWithArgs:')
        return

    def arrayDefArgBegin(self):
        self.beginMethodBuffering()
        return
        
    def arrayDefArgEnd(self):
        self.addToMethodBody('%s, '%(self.popBuff()))            
        return

    def arrayDefEnd(self):
        self.addToMethodBody('Nil]')
        return
        