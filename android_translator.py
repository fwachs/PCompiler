import types, copy, type_inference, translator, os 

class TranslatorAndroid(translator.Translator):
    path = ''
    className = ''
    classFileHandler = None
    proxyFileHandler = None
    tabDepth = -1
    methodName = None
    definedMethods = {}
   
    def start(self):
        self.path = '/users/Rafa/Desarrollo/2clams/KitchenRage Android/src/com/twoclams/kitchenrage/game'
        
        protocolPath = '/users/Rafa/Desarrollo/2clams/KitchenRage Android/src/com/twoclams/framework'         
        if not os.path.exists(protocolPath):
            os.makedirs(protocolPath)        
                
        self.proxyFileHandler = open(protocolPath + '/ProxyProtocol.java', 'w+')
        self.proxyFileHandler.write('package com.twoclams.framework;\n\n')
        self.proxyFileHandler.write('import com.twoclams.Kalimba.DynamicTypes.Proxy;\n\n')
                
        self.proxyFileHandler.write("public interface ProxyProtocol {\n")        
        return
   
    def done(self):
        self.proxyFileHandler.write("}")
        self.proxyFileHandler.close();        
        return
    
    def beginFile(self, dirname, fileName):
        if not os.path.exists(self.path):
            os.makedirs(self.path)        
        return
    
    def endFile(self):
        return
    
    def beginClass(self, node):
        self.className = node[1]
        self.classFileHandler = open('%s/%s.java'%(self.path, self.className), 'w+')
        
        self.classFileHandler.write('package %s.%s.game;\n\n'%(self.companyIdentifier, self.projectName.lower()))
        self.classFileHandler.write('import com.twoclams.Kalimba.*;\n\n')
        self.classFileHandler.write('import com.twoclams.Kalimba.DynamicTypes.*;\n\n')
        
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
            interfaces = ' implements %s'%(interfaces)

        self.classFileHandler.write("public class %s extends %s%s {\n"%(self.className, extends, interfaces))
        
        return
    
    def endClass(self, node):
        self.classFileHandler.write("}\n")
        self.classFileHandler.close();
        self.classFileHandler = None
        return
    
    def getNativeType(self, type):
        return
    
    def beginMethod(self, node, returnsVoid):
        self.constructorCalledSuper = False
        
        self.methodName = node[1]
    
        methodName = self.methodName 

        sym = self.inferencer.thisScope.findSymbol(self.methodName)
            
        staticMode = ''
        if len(node) >= 5:
            for decoration in node[4]:
                if decoration == 'static':
                    staticMode = ' static'
                    sym.isStatic = True
                    break
                
        returnType = 'Proxy'
        if sym.returnsVoid:
            returnType = 'void'
            
        if methodName == self.className:
            returnType = ''

        funcString = '\n\tpublic%s %s %s('%(staticMode, returnType, methodName)
                    
        signature = None
        if node[1] != 0:
            signature = node[2][1]

            idx = 0
            if signature != None:                    
                if len(signature):
                    for arg in signature:
                        if idx > 0:
                            funcString = funcString + ', '
                        funcString = funcString + 'Proxy %s'%(arg[0][1])
                        idx += 1

        self.classFileHandler.write(funcString + ') \n\t{\n')

        if not self.definedMethods.has_key(methodName) and methodName != self.className and sym.isStatic == False:
            self.definedMethods[methodName] = methodName;
            
            if sym.returnsVoid:
                self.proxyFileHandler.write(funcString + ') {}\n')
            else:
                self.proxyFileHandler.write(funcString + ') { return Proxy.nullProxy(); }\n')
    
            return
    
    def emptyRet(self, node):
        return
        
    def endMethod(self, node):
        self.methodName = None
        self.classFileHandler.write('\t}\n')
        return
    
    def localId(self, name):
        self.classFileHandler.write(name)
        return
    
    def memberId(self, name):
        self.classFileHandler.write('this.%s'%(name))
        return
    
    def staticMemberId(self, name):
        self.classFileHandler.write('.%s'%(name))
        return
    
    def memberFunctionId(self, name):
        self.classFileHandler.write('this.%s'%(name))
        return
    
    def staticFunctionId(self, name):
        self.classFileHandler.write('%s'%(name))
        return
    
    def methodCallBegin(self, node):
        return
    
    def methodCallBeginArgs(self, argCnt, name, isGlobal):
        if name == 'initWithArgs':
            self.classFileHandler.write('(')
        else:
            self.classFileHandler.write('.%s('%(name))
        return
        
    def methodCallArgument(self, argIdx, argCnt):
        if argIdx < argCnt - 1:
            self.classFileHandler.write(', ');
        return
    
    def methodCallEnd(self, name, isGlobal):
        self.classFileHandler.write(')')
        return    
    
    def newObjectBegin(self, className):
        self.classFileHandler.write('new %s('%(className))
        return
    
    def newObjectArgument(self, argIdx):
        if argIdx > 0:
            self.classFileHandler.write(', ')
        return
    
    def newObjectEnd(self, argsCount):
        self.classFileHandler.write(')')
        return
    
    def intConstant(self, intConst):
        self.classFileHandler.write('Proxy.intProxy(%d)'%(intConst))
        return
    
    def floatConstant(self, floatConst):
        self.classFileHandler.write('Proxy.floatProxy(%f)'%(floatConst))
        return
    
    def stringConstant(self, stringConst):
        self.classFileHandler.write('Proxy.stringProxy(%s)'%(stringConst))
        return

    def nullConstant(self):
        self.classFileHandler.write('Proxy.nullProxy()')
        return
        
    def assignBegin(self):
        return
    
    def assignMiddle(self, operator):
        operatorName = ''
        if operator == '=':
            self.classFileHandler.write(' = ')
        else:
            if operator == '+=':
                operatorName = 'add2self'
            elif operator == '-=':
                operatorName = 'sub2self'
            elif operator == '*=':
                operatorName = 'mul2self'
            elif operator == '/=':
                operatorName = 'div2self'
            else:
                operatorName = 'copy'
    
            self.classFileHandler.write('.%s('%(operatorName))
        return
    
    def assignEnd(self, operator):
        if operator == '=':
            self.classFileHandler.write('.copy()')
        else:
            self.classFileHandler.write(')')
        return
    
    def retBegin(self):
        self.classFileHandler.write('return ')
        return
    
    def retEnd(self, node):
        return
    
    def statementBegin(self):
        self.tabDepth += 1
        if self.classFileHandler:
            self.classFileHandler.write(self.tabString(self.tabDepth))
        return
    
    def statementEnd(self):
        self.tabDepth -= 1
        if self.classFileHandler and self.methodName:
            self.classFileHandler.write(';\n')
        return
    
    def ifBegin(self):
        self.classFileHandler.write('if')
        return
    
    def ifExpBegin(self):
        self.classFileHandler.write('(')
        return
    
    def ifExpEnd(self):
        self.classFileHandler.write('.boolValue()) {\n')
        return
    
    def ifElse(self, isSingleStatement):
        if isSingleStatement:
            self.classFileHandler.write(self.tabString(self.tabDepth) + '} else ')
        else:
            self.classFileHandler.write(self.tabString(self.tabDepth) + '} else {\n')
        return
    
    def ifEnd(self, isSingleStatement):
        if not isSingleStatement:
            self.classFileHandler.write(self.tabString(self.tabDepth) + '}')
        return
    
    def varDefBegin(self, name, isStatic, isWeak, isPublic, isFinal, cnt):
        stat = ''
        pub = ''
        final = ''
        if isStatic:
            stat = 'static '
        if isPublic:
            pub = 'public '
        if isFinal:
            final = 'final '
            
        self.classFileHandler.write("%s%s%sProxy %s = "%(pub, stat, final, name))        
        
        if self.methodName:
            if not self.definedMethods.has_key(name) and isStatic == False:
                self.definedMethods[name] = name;
                self.proxyFileHandler.write('\n\tpublic Proxy %s;\n'%(name))
        return
    
    def varDefEnd(self, symbol):
        if not self.methodName:
            self.classFileHandler.write(';\n')
        return
    
    def binOpBegin(self):
        return
    
    def binOpOperand(self, operator):
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
        
        self.classFileHandler.write('.' + methodName + '(')
        return
    
    def binOpEnd(self, operator, fromType, toType):
        self.classFileHandler.write(')')
        return
    
    def unOpBegin(self):
        return
    
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
        
        self.classFileHandler.write('.%s()'%(methodName))
        return
    
    def forBegin(self):
        self.classFileHandler.write('for(')
        return
    
    def forCondition(self):
        self.classFileHandler.write('; ')
        return
    
    def forStep(self):
        self.classFileHandler.write('.boolValue(); ')
        return
    
    def forBlock(self):
        self.classFileHandler.write(') {\n')
        return
    
    def forEnd(self):
        self.classFileHandler.write(self.tabString(self.tabDepth) + '}')
        return
    
    def whileBegin(self):
        self.classFileHandler.write('while(')
        return
    
    def whileBlock(self):
        self.classFileHandler.write('.boolValue()) {\n')
        return
    
    def whileEnd(self):
        self.classFileHandler.write(self.tabString(self.tabDepth) + '}')
        return
    
    def blockBegin(self, varDef, argList):
        final = ''
        if varDef[1] == 'const':
            final = 'final '
            
        self.classFileHandler.write('%sCodeBlock %s = new CodeBlock() {\n'%(final, varDef[2][0][1][1]))
        self.tabDepth += 1;
        self.classFileHandler.write(self.tabString(self.tabDepth) + 'public Proxy perform(')
        if argList:
            idx = 0
            for v in argList:
                if idx > 0:
                    self.classFileHandler.write(', ')
                self.classFileHandler.write('Proxy %s'%(v[1]))
        self.classFileHandler.write(') {\n')
        return
    
    def blockEnd(self):
        self.classFileHandler.write(self.tabString(self.tabDepth) + '}\n')
        self.tabDepth -= 1;        
        self.classFileHandler.write(self.tabString(self.tabDepth) + '}')        
        return

    def continueStmt(self):
        self.classFileHandler.write('continue')
        return
    
    def breakStmt(self):
        self.classFileHandler.write('break')
        return

    def this(self):
        self.classFileHandler.write('this')
        return

    def super(self):
        self.classFileHandler.write('super')
        return

    def point(self):
        self.classFileHandler.write('.')
        return

    def space(self):
        self.classFileHandler.write(' ')
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
    
    def arrayDefArgEnd(self):
        return

    def arrayDefEnd(self):
        return
    