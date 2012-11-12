import types, copy, type_inference, translator 

class TranslatorIOS(translator.Translator):
    mFileHandler = None
    hFileHandler = None
    hFileVarDefs = ''
    hFileMethodDefs = ''
    mFileMethodDefs = ''
    mFileMethodBody = ''
    definedIds = []
    className = None
    methodName = None
    tabDepth = -1
    isInsideACall = False
        
    def beginFile(self, fileName):
        mFileName = fileName.replace('.as', '.m')
        hFileName = fileName.replace('.as', '.h')
        path = ''
        
        self.mFileHandler = open(path + mFileName, 'w+')
        self.hFileHandler = open(path + hFileName, 'w+')
        return
    
    def endFile(self):
        self.mFileHandler.close()
        self.mFileHandler = None
        
        self.hFileHandler.close()
        self.hFileHandler = None
        return
    
    def beginClass(self, node):
        self.className = node[1]
        
        self.mFileHandler.write('@implementation %s\n\n'%(self.className))
        return
    
    def endClass(self, node):
        self.hFileHandler.write('@interface %s {\n%s}\n\n%s\n@end\n\n'%(self.className, self.hFileVarDefs, self.hFileMethodDefs))
        self.mFileHandler.write('%s@end\n\n'%(self.mFileMethodDefs))
        self.className = None
        self.methodName = None
        self.hFileVarDefs = ''
        self.hFileMethodDefs = ''
        self.mFileMethodDefs = ''
        self.mFileMethodBody = ''
        return
    
    def getNativeType(self, itype):
        if itype == 'string':
            return 'NSString *'
        elif itype == 'int':
            return 'int'
        elif itype == 'id':
            return 'id'
        elif not itype:
            return 'UNKNOWN_TYPE'
        else:
            return '%s *'%(itype)
    
    def beginMethod(self, node):
        if self.methodName == 'init':
            self.endMethod([0, 0])
                        
        funcString = ''
        signature = None
        if node[1] == 0:
            funcString = '- (id)init'
            self.methodName = 'init'
        else:
            self.methodName = node[1]
            
            signature = node[2][1]
            retType = node[2][2]
            
            if self.methodName == self.className:
                self.methodName = 'init'
                retType = 'id'
        
            funcString = '- (%s)%s'%(self.getNativeType(retType), self.methodName)
            if signature != None:
                    
                funcString = '- (%s)%s'%(self.getNativeType(retType), self.methodName)
                if len(signature):
                    idx = 0
                    for arg in signature:
                        argType = ''
                        if len(arg[0]) > 3:
                            argType = arg[0][3]
                            
                        funcString += 'WithArg%d:(%s)%s'%(idx, self.getNativeType(argType), arg[0][1])
                        idx = idx + 1     
                        if idx < len(signature):
                            funcString += ' '
                
                    
        self.hFileMethodDefs += funcString + ';\n'
        
        self.mFileMethodBody += funcString + '\n{\n'   
        
        if self.methodName == 'init':
            if signature:
                self.mFileMethodBody += '\tself = [self init];\n'        
            else:
                self.mFileMethodBody += '\tself = [super init];\n'        
            self.mFileMethodBody += '\tif(self) {\n'        
        return
    
    def emptyRet(self, node):
        self.statementBegin()

        if node[1] == 0:
            self.mFileMethodBody += 'return self'
        else:
            self.mFileMethodBody += 'return Nil'
            
        self.statementEnd()
        return
        
    def endMethod(self, node):
        if self.methodName == 'init':
            self.mFileMethodBody += '\t}\n'        
            self.mFileMethodBody += '\treturn self;\n'
                    
        self.mFileMethodBody += '}\n\n'
        
        self.mFileHandler.write(self.mFileMethodBody)
        self.mFileMethodBody = ''
        
        self.methodName = None           
        
        self.tabDepth = 0
        return
    
    def localId(self, name):
        self.mFileMethodBody += name
        return
    
    def memberId(self, name):
        if name not in self.definedIds:
            self.definedIds.append(name)
        
        self.mFileMethodBody += 'self.%s'%(name)
        return
    
    def staticMemberId(self, name):
        if name not in self.definedIds:
            self.hFileMethodDefs = '+ (id)%s;\n'%(name) + self.hFileMethodDefs
            self.mFileMethodDefs = '+ (id)%s\n{\n\tstatic id _%s;\n\n\treturn _%s;\n}\n\n'%(name, name, name) + self.mFileMethodDefs
            self.definedIds.append(name)
        return
    
    def memberFunctionId(self, name):
        self.mFileMethodBody += 'self %s'%(name)
        return
    
    def staticFunctionId(self, name):
        return
    
    def methodCallBegin(self):
        self.mFileMethodBody += '['
        self.isInsideACall = True
        return
    
    def methodCallArgument(self, argIdx):
        self.isInsideACall = False
        if argIdx > 0:
            self.mFileMethodBody += ' '
        self.mFileMethodBody += 'WithArg%d:'%(argIdx)
        return
    
    def methodCallEnd(self):
        self.isInsideACall = False
        self.mFileMethodBody += ']'
        return
    
    def newObjectBegin(self, className):
        self.mFileMethodBody += '[[alloc %s] init'%(className)
        return
    
    def newObjectArgument(self, argIdx):
        if argIdx > 0:
            self.mFileMethodBody += ' '
        self.mFileMethodBody += 'WithArg%d:'%(argIdx)
        return
    
    def newObjectEnd(self):
        self.mFileMethodBody += ']'
        return
    
    def intConstant(self, intConst):
        self.mFileMethodBody += '%d'%(intConst)
        return
    
    def floatConstant(self, floatConst):
        self.mFileMethodBody += '%f'%(floatConst)
        return
    
    def stringConstant(self, stringConst):
        self.mFileMethodBody += '@' + stringConst
        return

    def nullConstant(self):
        self.mFileMethodBody += 'Nil'
        return
        
    def assignBegin(self):
        return
    
    def assignMiddle(self, operator):
        self.mFileMethodBody += ' %s '%(operator)
        return
    
    def assignEnd(self):
        return
    
    def retBegin(self):
        self.mFileMethodBody += 'return '
        return
    
    def retEnd(self):
        return
    
    def statementBegin(self):
        self.tabDepth += 1
        self.mFileMethodBody += self.tabString(self.tabDepth)
        return
    
    def statementEnd(self):
        self.tabDepth -= 1
        
        if self.methodName:
            self.mFileMethodBody += ';\n'
        return
    
    def ifBegin(self):
        self.mFileMethodBody += 'if'
        return
    
    def ifExpBegin(self):
        self.mFileMethodBody += '('
        return
    
    def ifExpEnd(self):
        self.mFileMethodBody += ') {\n'
        return
    
    def ifElse(self, isSingleStatement):
        if isSingleStatement:
            self.mFileMethodBody += self.tabString(self.tabDepth) + '} else '
        else:
            self.mFileMethodBody += self.tabString(self.tabDepth) + '} else {\n'
        return
    
    def ifEnd(self, isSingleStatement):
        if not isSingleStatement:
            self.mFileMethodBody += self.tabString(self.tabDepth) + '}'
        return
    
    def varDefBegin(self, name, itype, cnt):
        if not self.methodName:
            self.beginMethod([0, 0])
                        
        if self.methodName == 'init':
            self.hFileVarDefs += '\t%s %s;\n'%(self.getNativeType(itype), name)
            self.mFileMethodBody += '\t\tself.%s = '%(name)
        else:
            if cnt == 0:
                self.mFileMethodBody += '%s '%(self.getNativeType(itype))
            else:
                self.mFileMethodBody += ', '            
                
            self.mFileMethodBody += '%s = '%(name)
        return
    
    def varDefEnd(self):
        return
    
    def binOp(self, operator):
        self.mFileMethodBody += ' %s '%(operator)
        return
    
    def unOp(self, operator):
        self.mFileMethodBody += '%s'%(operator)
        return
    
    def forBegin(self):
        self.mFileMethodBody += 'for('        
        return
    
    def forCondition(self):
        self.mFileMethodBody += '; '        
        return
    
    def forStep(self):
        self.mFileMethodBody += '; '        
        return
    
    def forBlock(self):
        self.mFileMethodBody += ') {\n'        
        return
    
    def forEnd(self):
        self.mFileMethodBody += self.tabString(self.tabDepth) + '}'
        return
    
    def whileBegin(self):
        self.mFileMethodBody += 'while('        
        return
    
    def whileBlock(self):
        self.mFileMethodBody += ') {\n'        
        return
    
    def whileEnd(self):
        self.mFileMethodBody += self.tabString(self.tabDepth) + '}'
        return
    
    def continueStmt(self):
        self.mFileMethodBody += 'continue'
        return
    
    def breakStmt(self):
        self.mFileMethodBody += 'break'
        return

    def this(self):
        self.mFileMethodBody += 'self'
        return

    def point(self):
        self.mFileMethodBody += '.'
        return

    def space(self):
        self.mFileMethodBody += ' '
        return
        