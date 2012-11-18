import types, copy, type_inference, translator 

class TranslatorIOS(translator.Translator):
    mFileHandler = None
    hFileHandler = None
    hFileVarDefs = ''
    hFileMethodDefs = ''
    mFileMethodDefs = ''
    mFileMethodBody = ''
    tempBodyBuf = []
    definedIds = []
    className = None
    methodName = None
    tabDepth = -1
    isInsideACall = False
    
    def addToMethodBody(self, text):
        if len(self.tempBodyBuf) == 0:
            self.mFileMethodBody += text
        else:
            self.tempBodyBuf[-1] += text
        
    def beginMethodBuffering(self):
        self.tempBodyBuf.append('')
        
    def getCurrentBuff(self):
        return self.tempBodyBuf.pop()
        
    def enMethodBuffering(self):
        if len(self.tempBodyBuf) > 0:
            self.mFileMethodBody += self.tempBodyBuf.pop()
        
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
        extends = ' : NSObject'
        if node[2] and node[2][0]:
            extends = ' : %s'%(node[2][0][1])
        self.hFileHandler.write('@interface %s%s {\n%s}\n\n%s\n@end\n\n'%(self.className, extends, self.hFileVarDefs, self.hFileMethodDefs))
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
        elif itype == 'void':
            return 'void'
        elif not itype:
            return 'UNKNOWN_TYPE'
        else:
            return '%s *'%(itype)
    
    def beginMethod(self, node, returnsVoid):
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
            
            if returnsVoid:
                retType = 'void'
            
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
        
        self.addToMethodBody(funcString + '\n{\n'   )
        
        if self.methodName == 'init':
            if signature:
                self.addToMethodBody('\tself = [self init];\n'        )
            else:
                self.addToMethodBody('\tself = [super init];\n'        )
            self.addToMethodBody('\tif(self) {\n'        )
        return
    
    def emptyRet(self, node):
        self.statementBegin()

        if node[1] == 0:
            self.addToMethodBody('return self')
        else:
            self.addToMethodBody('return Nil')
            
        self.statementEnd()
        return
        
    def endMethod(self, node):
        if self.methodName == 'init':
            self.addToMethodBody('\t}\n'        )
            self.addToMethodBody('\treturn self;\n')
                    
        self.addToMethodBody('}\n\n')
        
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
        self.addToMethodBody('[')
        self.isInsideACall = True
        return
    
    def methodCallArgument(self, argIdx):
        self.isInsideACall = False
        if argIdx > 0:
            self.addToMethodBody(' ')
        self.addToMethodBody('WithArg%d:'%(argIdx))
        return
    
    def methodCallEnd(self):
        self.isInsideACall = False
        self.addToMethodBody(']')
        return
    
    def newObjectBegin(self, className):
        self.addToMethodBody('[[alloc %s] init'%(className))
        return
    
    def newObjectArgument(self, argIdx):
        if argIdx > 0:
            self.addToMethodBody(' ')
        self.addToMethodBody('WithArg%d:'%(argIdx))
        return
    
    def newObjectEnd(self):
        self.addToMethodBody(']')
        return
    
    def intConstant(self, intConst):
        self.addToMethodBody('%d'%(intConst))
        return
    
    def floatConstant(self, floatConst):
        self.addToMethodBody('%f'%(floatConst))
        return
    
    def stringConstant(self, stringConst):
        self.addToMethodBody('@' + stringConst)
        return

    def nullConstant(self):
        self.addToMethodBody('Nil')
        return
        
    def assignBegin(self):
        return
    
    def assignMiddle(self, operator):
        self.addToMethodBody(' %s '%(operator))
        return
    
    def assignEnd(self):
        return
    
    def retBegin(self):
        self.addToMethodBody('return ')
        return
    
    def retEnd(self):
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
    
    def varDefBegin(self, name, itype, cnt):
        if not self.methodName:
            self.beginMethod([0, 0], False)
                        
        if self.methodName == 'init':
            self.hFileVarDefs += '\t%s %s;\n'%(self.getNativeType(itype), name)
            self.addToMethodBody('\t\tself.%s = '%(name))
        else:
            if cnt == 0:
                self.addToMethodBody('%s '%(self.getNativeType(itype)))
            else:
                self.addToMethodBody(', '            )
                
            self.addToMethodBody('%s = '%(name))
        return
    
    def varDefEnd(self):
        return
    
    def binOp(self, operator):
        self.addToMethodBody(' %s '%(operator))
        return
    
    def unOp(self, operator):
        self.addToMethodBody('%s'%(operator))
        return
    
    def forBegin(self):
        self.addToMethodBody('for('        )
        return
    
    def forCondition(self):
        self.addToMethodBody('; '        )
        return
    
    def forStep(self):
        self.addToMethodBody('; '        )
        return
    
    def forBlock(self):
        self.addToMethodBody(') {\n'        )
        return
    
    def forEnd(self):
        self.addToMethodBody(self.tabString(self.tabDepth) + '}')
        return
    
    def whileBegin(self):
        self.addToMethodBody('while('        )
        return
    
    def whileBlock(self):
        self.addToMethodBody(') {\n'        )
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
        self.addToMethodBody(' objectAtIndex:')
        return
    
    def arrayAccessEnd(self):
        self.addToMethodBody(']')
        return
    
    def arrayDefBegin(self):
        self.addToMethodBody('[NSMutableArray arrayWithObjects:')
        return

    def arrayDefArgBegin(self):
        self.beginMethodBuffering()
        return
        
    def arrayDefArgEnd(self, argType):
        if argType == 'int':
            self.addToMethodBody('[NSNumber numberWithInt:%s], '%(self.getCurrentBuff()))
        elif argType == 'float':
            self.addToMethodBody('[NSNumber numberWithFloat:%s], '%(self.getCurrentBuff()))
        else:
            self.addToMethodBody('%s, '%(self.getCurrentBuff()))            
        return

    def arrayDefEnd(self):
        self.addToMethodBody('Nil]')
        return
        