import types, copy, type_inference, translator, os 

class TranslatorIOS(translator.Translator):
    mFileHandler = None
    hFileHandler = None
    hFileVarDefs = ''
    hFilePropDefs = ''
    hFileMethodDefs = ''
    mFileMethodDefs = ''
    mFileMethodBody = ''
    tempBodyBuf = []
    definedIds = []
    className = None
    methodName = None
    tabDepth = -1
    isInsideACall = False
    localVars = None
    iVars = None
    
    def addToMethodBody(self, text):
        if len(self.tempBodyBuf) == 0:
            self.mFileMethodBody += text
        else:
            self.tempBodyBuf[-1] += text
        
    def beginMethodBuffering(self):
        self.tempBodyBuf.append('')
        
    def popBuff(self):
        return self.tempBodyBuf.pop()
        
    def endMethodBuffering(self):
        if len(self.tempBodyBuf) > 0:
            self.mFileMethodBody += self.tempBodyBuf.pop()
        
    def beginFile(self, dirname, fileName):
        
        path = dirname.replace('projects/housewifewars', 'projects/housewifewars/ios')        
        if not os.path.exists(path):
            os.makedirs(path)
        
        mFileName = fileName.replace('.as', '.m')
        hFileName = fileName.replace('.as', '.h')
        
        self.mFileHandler = open('%s/%s'%(path, mFileName), 'w+')
        self.hFileHandler = open('%s/%s'%(path, hFileName), 'w+')
        
        self.hFileHandler.write('#import <Foundation/Foundation.h>\n#import "proxy.h"\n\n')
        self.mFileHandler.write('#import "%s"\n#import "types.h"\n\n'%(hFileName))
        return
    
    def endFile(self):
        self.mFileHandler.close()
        self.mFileHandler = None
        
        self.hFileHandler.close()
        self.hFileHandler = None
        return
    
    def done(self):
        f = open('projects/test/CustomProxyProtocol.h', 'w+')
        
        f.write('#import <Foundation/Foundation.h>\n')
        f.write('@protocol CustomProxyProtocol <NSObject>\n\n')
                
        definedSymbols = {}
        
        for cls in self.inferencer.symbolsStack.children:
            for child in cls.children:
                if not definedSymbols.has_key(child.name):
                    definedSymbols[child.name] = child.name;
                    
                    if not child.isStatic:
                        if child.isVar:
                            f.write('\t@property (strong) Proxy *%s;\n'%(child.name))
                        else:
                            f.write('\t@property (strong) MethodCall %s;\n'%(child.name))
                            f.write('\t- (Proxy *)%s:(Proxy *)firstArg, ...;\n'%(child.name))
        
        f.write('\n@end\n')
        
        f.close()
                
        return
    
    def beginClass(self, node):
        self.className = node[1]
        
        self.mFileHandler.write('@implementation %s\n\n'%(self.className))
        
        symbol = self.inferencer.symbolsStack.findSymbol(self.className)
        for child in symbol.children:
            if not child.isStatic:
                self.mFileHandler.write('@synthesize %s;\n'%(child.name))
        self.mFileHandler.write('\n')
        return
    
    def endClass(self, node):
        extends = ' : Proxy'
        if node[2] and node[2][0]:
            extends = ' : %s'%(node[2][0][1])

        self.buildMethodProperties()
        self.buildStaticAccessors()
    
        self.hFileHandler.write('@interface %s%s {\n%s}\n\n%s\n\n%s\n@end\n\n'%(self.className, extends, self.hFileVarDefs, self.hFilePropDefs, self.hFileMethodDefs))
        self.mFileHandler.write('%s\n%s\n@end\n\n'%(self.mFileMethodDefs, self.mFileMethodBody))
        self.className = None
        self.methodName = None
        self.hFileVarDefs = ''
        self.hFilePropDefs = ''
        self.hFileMethodDefs = ''
        self.mFileMethodDefs = ''
        self.mFileMethodBody = ''
        return
    
    def buildMethodProperties(self):
        methodsDef = '\tNSMutableDictionary *newM = [NSMutableDictionary dictionaryWithDictionary:self.methods];\n'
        methodsDef += '\t[newM setValuesForKeysWithDictionary:[NSDictionary dictionaryWithObjectsAndKeys:'
        self.addToMethodBody('- (void)defineMethods\n{\n\t__weak typeof(self) weakSelf = self;\n\n\t[super defineMethods];\n\n');
        symbol = self.inferencer.symbolsStack.findSymbol(self.className)
        for child in symbol.children:
            if not child.isVar: 
                selfTarget = 'weakSelf'
                if not child.isStatic:
                    self.addToMethodBody('\tself.%s = ^(Proxy *firstArg, ...)\n\t{\n\t\tva_list args;\n\t\tva_start(args, firstArg);\n\n\t\tProxy *ret = [%s _%s:firstArg args:args];\n\t\tva_end(args);\n\n\t\treturn ret;\n\t};\n\n'%(child.name, selfTarget, child.name))
                    methodsDef += 'self.%s, @"%s", '%(child.name, child.name)
        self.addToMethodBody(methodsDef + 'Nil]];\n\tself.methods = newM;\n}\n\n')
        return
    
    def buildStaticAccessors(self):
        symbol = self.inferencer.symbolsStack.findSymbol(self.className)
        for child in symbol.children:
            if child.isStatic:
                if child.isVar:
                    self.addToMethodBody('static Proxy *_%s;\n\n'%(child.name))
                    self.addToMethodBody('+ (Proxy*)%s\n{\n\t@synchronized(self)\n\t{\n\t\tif(_%s == Nil) {\n\t\t\t_%s = %s;\n\t\t}\n\t}\n\n\treturn _%s;\n}\n\n'%(child.name, child.name, child.name, child.staticInitializer, child.name))
                    self.addToMethodBody('+ (void)set%s:(Proxy*)newValue\n{\n\t_%s = newValue;\n}\n\n'%(child.name.title(), child.name))
                    self.hFileMethodDefs += '+ (Proxy*)%s;\n'%(child.name)
                    self.hFileMethodDefs += '+ (void)set%s:(Proxy*)newValue;\n'%(child.name.title())
                else:
                    self.addToMethodBody('+ (MethodCall)%s\n{\n\tMethodCall m = ^(Proxy *firstArg, ...)\n\t{\n\t\tva_list args;\n\t\tva_start(args, firstArg);\n\n\t\tProxy *ret = [%s _%s:firstArg args:args];\n\t\tva_end(args);\n\n\t\treturn ret;\n\t};\n\n\treturn m;\n}\n\n'%(child.name, self.className, child.name))                    
                    self.hFileMethodDefs += '+ (MethodCall)%s;\n'%(child.name)
        return

    def getNativeType(self, itype):
        return 'Proxy *'
    
    def beginMethod(self, node, returnsVoid):
        if self.methodName == 'init':
            self.endMethod([0, 0])
                        
        funcString = ''
        if not self.className:
            self.methodName = node[1]
            sym = self.inferencer.symbolsStack.findSymbol(self.methodName)
            sym.isGlobal = True
            self.beginMethodBuffering()
            self.addToMethodBody('Proxy *%s(Proxy *firstArg, ...)\n{\n'%(self.methodName))
        else :
            if node[1] == 0:
                funcString = '- (id)init'
                self.methodName = 'init'
            else:
                self.methodName = node[1]
                
                staticMode = '-'
                if len(node) >= 5:
                    for decoration in node[4]:
                        if decoration == 'static':
                            staticMode = '+'
                            self.inferencer.thisScope.findSymbol(self.methodName).isStatic = True
                            break
                    
                funcString = '%s (Proxy *)_%s:(Proxy *)firstArg args:(va_list)args'%(staticMode, self.methodName)
                if staticMode == '-':
                    self.hFileMethodDefs += '@property (strong) MethodCall %s;\n'%(self.methodName)
                else:
                    self.hFileMethodDefs += '+ (Proxy*)%s:(Proxy *)firstArg, ...;\n'%(self.methodName)
                
            
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
                            self.addToMethodBody('\tProxy *%s = va_arg(args, Proxy*);\n'%(arg[0][1]))
                        idx += 1
                self.addToMethodBody('\n')
        
        if self.methodName == 'init':
            if signature:
                self.addToMethodBody('\tself = [self init];\n')
            else:
                self.addToMethodBody('\tself = [super init];\n')
            self.addToMethodBody('\tif(self) {\n')
        return
    
    def emptyRet(self, node):
        return
        
    def endMethod(self, node):
        if self.methodName == 'init':
            self.addToMethodBody('\t}\n')
            self.addToMethodBody('\treturn self;\n')
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
                    sym = self.inferencer.thisScope.findSymbol(self.methodName)
                    if sym and sym.isStatic:
                        staticMode = '+'
                        
                    self.addToMethodBody('%s (Proxy *)%s:(Proxy *)firstArg, ...\n{\n\tva_list args;\n\tva_start(args, firstArg);\n\n\tProxy *ret = [self _%s:firstArg args:args];\n\n\tva_end(args);\n\n\treturn ret;\n}\n\n'%(staticMode, self.methodName, self.methodName))
        
        self.mFileHandler.write(self.mFileMethodBody)
        self.mFileMethodBody = ''
        
        self.methodName = None           
        
        self.tabDepth = 0
        return
    
    def localId(self, name):
        self.addToMethodBody(name)
        return
    
    def memberId(self, name):
        if name not in self.definedIds:
            self.definedIds.append(name)
        
        self.addToMethodBody('self.%s'%(name))
        return
    
    def staticMemberId(self, name):
        if name not in self.definedIds:
            self.hFileMethodDefs = '+ (id)%s;\n'%(name) + self.hFileMethodDefs
            self.mFileMethodDefs = '+ (id)%s\n{\n\tstatic id _%s;\n\n\treturn _%s;\n}\n\n'%(name, name, name) + self.mFileMethodDefs
            self.definedIds.append(name)
        return
    
    def memberFunctionId(self, name):
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
            self.addToMethodBody('[' + self.popBuff())
        self.beginMethodBuffering()
        return
        
    def methodCallArgument(self, argIdx):
        self.isInsideACall = False
        self.addToMethodBody(', ')
        return
    
    def methodCallEnd(self, name, isGlobal):
        self.isInsideACall = False
        if isGlobal:
            self.addToMethodBody('%s(%sNil)'%(name, self.popBuff()))
        else:
            self.addToMethodBody(' %s:%sNil]'%(name, self.popBuff()))
        return
    
    def newObjectBegin(self, className):
        self.addToMethodBody('[[%s alloc] init].%s('%(className, className))
        return
        
    def newObjectArgument(self, argIdx):
        if argIdx > 0:
            self.addToMethodBody(', ')
        return
    
    def newObjectEnd(self, argsCount):
        if argsCount > 0:
            self.addToMethodBody(', ')
        self.addToMethodBody('Nil)')
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
        self.addToMethodBody('(')
        return
    
    def ifExpEnd(self):
        self.addToMethodBody(') {\n')
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
        if not self.methodName:
            self.beginMethod([0, 0], False)
                        
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
            symbol.staticInitializer = self.popBuff()
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
        self.addToMethodBody('; ')
        return
    
    def forStep(self):
        self.addToMethodBody('; ')
        return
    
    def forBlock(self):
        self.addToMethodBody(') {\n')
        return
    
    def forEnd(self):
        self.addToMethodBody(self.tabString(self.tabDepth) + '}')
        return
    
    def whileBegin(self):
        self.addToMethodBody('while(')
        return
    
    def whileBlock(self):
        self.addToMethodBody(') {\n')
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
        self.addToMethodBody('[[[Array alloc] init] Array:')
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
        