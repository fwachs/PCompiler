import aslex
import asyacc
from struct import pack,unpack
import os,sys,getopt,types
import ios_translator

glTranslator = ios_translator.Translator.createTranslator('ios')

outcode = ""
pc2line = []
funcPC2Name = []
debug = 1
funcs = []
internals = filter(lambda a:not a.strip().startswith('#') and a,open(os.path.join('data','funcs'),'rb').read().split('\r\n'))
internals = map(lambda a: a.split('#')[0].strip(), internals)
funcs.extend(internals)
#print funcs
extern = []
exFuncIndex = {}
consts = open(os.path.join('data','const'),'r').readlines()
constsMap = {}
defines = {}
for line in consts:
    if line.startswith('#define'):
        tok = line[len('#define'):].split()        
        if len(tok)==1:
            defines[tok[0]] = 1
            exec tok[0]+'='+'1'
        else:
            defines[tok[0]] = eval(tok[1])
            exec tok[0]+'='+tok[1]

opdict = {'in':5,'not in':4,'+':11,'-':12,'*':8,'/':9,'%':10,'<<':14,'>>':15,'&':16,'|':17,'^':18,
          '<':40,'>':41,'<=':42,'>=':43,'==':44,'!=':45}

errno = 0

def WARNING(code, **kw):
    if code==0:
        print "WARNING 0: line: %s  %s may not be initialized"%(kw['line'],kw['object'])
    
    
def ERROR(errcode, **kw):
    global errno
    errno += 1
    if errcode == 997:
        print "997: line %d: Nested function not supported yet"%(kw['line'])
    elif errcode == 998:
        print "998: line %d: Function %s is an built-in function, you may use another name or add 'this.' to call your function"%(kw['line'],kw['name'])
    elif errcode == 999:       
        print "999:  line %d: Access to Array %s must have one integer index"%(kw['line'],kw['name'])
    elif errcode == 1006:
        print "1006: line %d: A super expression can be used only inside class instance methods."%(kw['line'])
    elif errcode == 1023:
        print "1023: line %d: Incompatible override"%(kw['line'])
    elif errcode == 1024:
        print "1024: line %d: Overriding a function must use override attribute"%(kw['line'])
    elif errcode == 1038:
        print "1038: line %d: Target of break statement was not found"%(kw['line'])
    elif errcode == 1039:
        print "1039: line %d: Target of continue statement was not found"%(kw['line'])
    elif errcode == 1042:
        print "1042: line %d: The this keyword can only be used in instance methods"%(kw['line'])
    elif errcode == 1044:
        print "1044: line %d: Interface method %s not implemented by class %s"%(kw['line'], kw['interface'],kw['cls'])
    elif errcode == 1049:
        print "1049: line %d: Illegal assignment to variable %s specified as constant."%(kw['line'],kw['name'])
    elif errcode == 1119:
        print "1119: line %d: Access of possibly undefined property %s"%(kw['line'],kw['name'])
    elif errcode == 1120:
        print "1120: line %d: Variable %s is not defined"%(kw['line'],kw['name'])
    elif errcode == 1125:
        print "1125: line %d: Methods defined in an interface must not have a body"%(kw['line'])
    elif errcode == 1131:
        print "1131: line %d: Class must not be nested."%(kw['line'])
    elif errcode == 1136:
        print "1136: line %d: Incorrect number of arguments, expected %d"%(kw['line'],kw['num'])
    elif errcode == 1138:
        print "1138: line %d: Required parameters are not permitted after optional parameters"%(kw['line'])
    elif errcode == 1139:
        print "1139: line %d: Variable declarations are not permitted in interfaces"%(kw['line'])
    elif errcode == 1151:
        print "1151: line %d: A conflict exists with definition %s"%(kw['line'],kw['name'])       
    elif errcode == 1152:
        print "1152: line %d: A conflict exists with inherited definition %s"%(kw['line'],kw['name'])
    elif errcode == 1172:
        print "1172: line %d: Definition %s could not be found"%(kw['line'],kw['name'])
    elif errcode == 1190:
        print "1190: line %d: Base class was not found, not defined as class or is not a compile-time constant"%(kw['line'],kw['name'])
    elif errcode == 1193:
        print "1193: line %d: Interface definitions must not be nested within class or other interface definitions"%(kw['line'])
    elif errcode == 1203:
        print "1203: line %d: No default constructor found in base class %s"%(kw['line'],kw['basename'])
    else:
        print "ERROR: %s is not supported"%(kw['name'])

def changePC2line(pc):
    global pc2line    
    for i in range(len(pc2line)):
        if type(pc2line[i]) is not str and pc2line[i][0]>=pc:break
    while i<len(pc2line):
        pc2line[i][0]+=1
        i += 1
    
def fill(jump, dst=None):
    global outcode
    jumpdict = {2:25,3:26,49:36,50:37,38:35} 
    while(len(jump)>0):
        if not dst:
            dst = len(outcode)
        j = jump.pop()
        src = j[2]
        if -128<=dst-src<=127:
            outcode = outcode[:j[1]] + pack('b',dst-src) + outcode[j[1]+1:]
            return False
        else:
            if dst>src:
                dist = dst - src
            else:
                dist = dst-src-1
            changePC2line(j[1])
            outcode = outcode[:j[1]-1]+chr(jumpdict[j[0]])+pack('h',dist)+outcode[j[1]+1:]
            return True

def fill2(jump,dst=None):
    global outcode
    while(len(jump)>0):
        if not dst:
            dst = len(outcode)
        j = jump.pop()
        src = j[2]
        outcode = outcode[:j[1]] + pack('h',dst-src) + outcode[j[1]+2:]
        
scopechain = []
globalindex = 0
localindex = 0
__INIT__ = 0
__BASEINIT__ = 1
__CLASSNAME__ = 468
def findInScopeChain(name):
    global scopechain
    for scopei in range(len(scopechain)-1,-1,-1):        
        value = scopechain[scopei][1].get(name)
        if value:
            return (scopechain[scopei][0],value)
    return None

def isInCls():
    global scopechain
    ret = [None,0]
    for scopei in range(len(scopechain)-1,-1,-1):
        if type(scopechain[scopei][0]) is int:
            ret[0] = scopechain[scopei]
            break
        elif scopechain[scopei][0] == 'f':
            if type(scopechain[scopei][2][0]) is list and 'static' in scopechain[scopei][2][0]:
                ret[1] = 1
    return ret

def inConstructor():
    global scopechain
    for scopei in range(len(scopechain)-1,-1,-1):        
        if scopechain[scopei][0] == 'f' and scopechain[scopei][2][1][1]==__INIT__:
            return True
    return False

def getInheritScope(name):
    global scopechain    
    return scopechain[0][1].get(name)[1][1].get('INHERIT').copy()

def getClass(name):
    global scopechain
    return scopechain[0][1].get(name)[0]

def compareSig(funNode, oldfun):    
    if not funNode[2][1]:
        if oldfun[1][2][1]:
            ERROR(1023,line=funNode[2][3])
            return False
    else:
        if not oldfun[1][2][1] or len(funNode[2][1]) != len(oldfun[1][2][1]):
            ERROR(1023,line=funNode[2][3])
            return False     
    if not funNode[2][2]:
        if oldfun[1][2][2]:            
            ERROR(1023,line=funNode[2][3])
            return False       
    else:
        if not oldfun[1][2][2] or  funNode[2][2][0] != oldfun[1][2][2][0]:
            ERROR(1023,line=funNode[2][3])
            return False
    return True
    
def checkOverride(funNode, oldfun):    
    if len(funNode)<5 or 'override' not in funNode[4]:
        ERROR(1024,line=funNode[2][3])
        return False
    return compareSig(funNode, oldfun)

def declBaseConstructor(scope):
    global outcode   
    genNode(['id',scope[1]['BASE']])
    outcode += chr(71)+pack('b',__INIT__)
    if -128<=scope[0]<=127:
        outcode += chr(54) + pack('b',scope[0])
    else:
        outcode += chr(32) + pack('h',scope[0])
    outcode += chr(72)+pack('b',__BASEINIT__)

def hasNoSuper(stmts):
    if not stmts: return True
    found = None
    s = None
    for i in range(len(stmts)):        
        if stmts[i][0] == 'super':
            found = i
            s = stmts[i]
            break   
    if s:
        stmts[found] = ['call','super',s[1],s[2]]
        return False    
    return True

def getClsHierarchy(baseName,line):
    global scopechain    
    if type(scopechain[0][1].get(baseName)[1][0]) is not int:
        ERROR(1190,line=line,name=baseName)   
    return scopechain[0][1].get(baseName)[1][2]

def getInBaseClass(currentClsScope,name):
    baseName = currentClsScope[1].get('BASE')
    baseScope = scopechain[0][1].get(baseName)
    if not baseScope:return None
    funScope = baseScope[1][1].get(name)
    if funScope: return funScope[1][2]
    return getInBaseClass(baseScope,name)

def declfun(node,isInter=False):
    global outcode,pc2line,scopechain,globalindex,localindex,funcs
    
    value = scopechain[-1][1].get(node[1])
    if value:
        ERROR(1151,line=node[2][3],name=node[1])
        return    
    inCls = False
    if scopechain[-1][0] == 'g':
        findex = globalindex
        scopechain[-1][1][node[1]] = [globalindex, node[:3],None,len(outcode)]
        if node[1] in ['initialize','start']:
            extern.append(node[1])
            exFuncIndex[node[1]] = findex
        globalindex += 1
    elif type(scopechain[-1][0]) is int:
        inCls = True        
        if scopechain[-1][1]['EXTEND'].get(node[1]):
            checkOverride(node, scopechain[-1][1]['EXTEND'].get(node[1]))                
            #baseindex = getClass(scopechain[-1][1]['BASE'])           
            #if -128<=baseindex<=127:            
                #outcode += chr(54)+pack('b',baseindex)
            #else:            
                #outcode += chr(32)+pack('h',baseindex)
            #key = funcs.index(node[1])
            #if key<256:
                #outcode += chr(71)+pack('B',key)
            #else:
                #outcode += chr(66)+pack('H',key)
            #if -128<=scopechain[-1][0]<=127:            
                #outcode += chr(54)+pack('b',scopechain[-1][0])
            #else:            
                #outcode += chr(32)+pack('h',scopechain[-1][0])           
            #if key not in funcs: funcs.append(key)
            #newKey = funcs.index(key)           
            #if key<256:
                #outcode += chr(72)+pack('B',newKey)
            #else:
                #outcode += chr(67)+pack('H',newKey)
            scopechain[-1][1]['EXTEND'].pop(node[1])            
        if scopechain[-1][1]['IMPL'].get(node[1]):
            compareSig(node, scopechain[-1][1]['IMPL'].get(node[1]))            
            scopechain[-1][1]['IMPL'].pop(node[1])
        attr = []
        if len(node)>4:
            attr = node[4]
        scopechain[-1][1][node[1]] = [attr, node[:3],None,len(outcode)]
    else: 
        #ERROR(997,line=node[2][3])
        findex = -localindex-1
        scopechain[-1][1][node[1]] = [-localindex-1, node[:3],None,len(outcode)]
        localindex += 1
    if not isInter:
        pc2line.append([len(outcode),node[2][3]])
        outcode += chr(75)+pack('i',4)
        if inCls:
            if len(node)>4 and 'static' in node[4]:
                pc2line.append([len(outcode),node[2][3]])
                outcode += chr(46)+chr(186)+chr(1)
            pc2line.append([len(outcode),node[2][3]])
            if -128<=scopechain[-1][0]<=127:            
                outcode += chr(54)+pack('b',scopechain[-1][0])
            else:            
                outcode += chr(32)+pack('h',scopechain[-1][0])
            if node[1] == __INIT__:
                key = __INIT__
            else:
                if node[1] not in funcs: funcs.append(node[1])
                key = funcs.index(node[1])
            pc2line.append([len(outcode),node[2][3]])
            if key<256:                
                outcode += chr(72)+pack('B',key)
            else:
                outcode += chr(67)+pack('H',key)
            pc2line.append([len(outcode),node[2][3]])
            if -128<=scopechain[-1][0]<=127:            
                outcode += chr(54)+pack('b',scopechain[-1][0])
            else:            
                outcode += chr(32)+pack('h',scopechain[-1][0])
            pc2line.append([len(outcode),node[2][3]])
            if key<256:                
                outcode += chr(71)+pack('B',key)
            else:
                outcode += chr(66)+pack('H',key)
            pc2line.append([len(outcode),node[2][3]])
            if -128<=scopechain[-1][0]<=127:            
                outcode += chr(54)+pack('b',scopechain[-1][0])
            else:            
                outcode += chr(32)+pack('h',scopechain[-1][0])
            hierarchy = scopechain[-1][2]
            if node[1] == __INIT__:
                fname = str(hierarchy)+'__INIT__'
            else:                
                fname = str(hierarchy)+node[1]
            if fname not in funcs: funcs.append(fname)
            key = funcs.index(fname)
            pc2line.append([len(outcode),node[2][3]])
            if key<256:                
                outcode += chr(72)+pack('B',key)
            else:
                outcode += chr(67)+pack('H',key)
        elif -128<=findex<=127:
            pc2line.append([len(outcode),node[2][3]])
            outcode += chr(55)+pack('b',findex)        
        else:
            pc2line.append([len(outcode),node[2][3]])
            outcode += chr(27)+pack('h',findex) 
    #scopechain[-1][1][node[1]][2] = scope    
    return scopechain[-1][1][node[1]] 

def declcls(node, isInter = False):
    global outcode,scopechain,globalindex,debug  
    #if scopechain[-1][0] != 'g':
        #if isInter:
            #ERROR(1193,line=node[4])            
        #else:
            #ERROR(1131,line=node[4])
        #return
    base = None
    implements = None
    size = 0
    scope= (globalindex,{},1)
    
    scope[1]['EXTEND'] = {}
    scope[1]['IMPL'] = {}
    if node[2]:
        if isInter:
            implements = []
            for baseInter in node[2]:
                implements.append(baseInter[1])
                scope[1]['EXTEND'].update(getInheritScope(baseInter[1]))
        else:
            if node[2][0]:
                genNode(node[2][0])
                base = node[2][0][1]
                scope[1]['EXTEND'] = getInheritScope(base)
                scope = scope[0], scope[1], getClsHierarchy(base,node[2][0][2])+1                
                size += 1
            if node[2][1]:
                implements = []            
                for interface in node[2][1]:                    
                    implements.append(interface[1])
                    scope[1]['IMPL'].update(getInheritScope(interface[1]))    
    scope[1]['BASE'] = base
    scope[1]['INTERFACE'] = implements    
    if scopechain[-1][1].get(node[1]):
        ERROR(1151,line=node[4],name=node[1])
    scopechain[-1][1][node[1]] = [globalindex,scope]    
    if not isInter:       
        pc2line.append([len(outcode),node[4]])
        outcode += chr(69)+pack('b',size)        
        pc2line.append([len(outcode),node[4]])
        if -128<=globalindex<=127:
            outcode += chr(55)+pack('b',globalindex)
        else:
            outcode += chr(27)+pack('h',globalindex)
        if debug:
            pc2line.append([len(outcode),node[4]])
            outcode += chr(34)+pack('h',len(node[1]))+node[1]
            pc2line.append([len(outcode),node[4]])
            if -128<=globalindex<=127:
                outcode += chr(54)+pack('b',globalindex)
            else:
                outcode += chr(32)+pack('h',globalindex)
            pc2line.append([len(outcode),node[4]])
            outcode += chr(67)+pack('h',__CLASSNAME__)
    globalindex += 1
    initdef = []
    init = []
    constructor = None
    todel = []
    staticvars = []
    caninherit = {}
    if node[3]:
        for decl in node[3]:
            if decl[0] == 'vardef':
                if isInter:
                    ERROR(1139,line=decl[3])
                    continue            
                attr = [] 
                if len(decl)>4:
                    attr = decl[4]
                for n in decl[2]:
                    value = scope[1].get(n[1][1])
                    if value:
                        ERROR(1151,line=decl[3],name=n[1][1])
                        continue
                    if scope[1].get('EXTEND') and scope[1]['EXTEND'].get(n[1][1]):
                        ERROR(1152,line=decl[3], name=n[1][1])                                    
                n[0] = decl[1]                       
                scope[1][n[1][1]] = [attr,n]
                if len(decl)<5 or 'static' not in decl[4]:
                    caninherit[n[1][1]] = [attr+['inherit'],n]
                if n[2]:                    
                    if len(decl)>4 and 'static' in decl[4]:                        
                        staticvars.append(['assign','=',['id',n[1][1],n[1][-1]],n[2]])
                    else:                        
                        initdef.append(['assign','=',['id',n[1][1],n[1][-1]],n[2]])
                todel.append(decl)
            elif decl[0] == 'fundef':
                if isInter and decl[3]:
                    ERROR(1125, line=decl[2][3])
                    continue
                if decl[1] == node[1] :
                    constructor = decl
                    decl[1] = __INIT__                
                scopechain.append(scope)
                f = declfun(decl,isInter)                
                if 'static' not in f[0] and decl[1] != __INIT__:
                    f[0].append('inherit')
                    caninherit[decl[1]] = f
                scope = scopechain.pop()
            elif decl[0] == 'interface':
                ERROR(1193,line=decl[4])
            else:
                init.append(decl)
                todel.append(decl)
    baseConstructor = None
    if scope[1]['EXTEND'].get(__BASEINIT__):
        #declBaseConstructor(scope)
        baseConstructor = scope[1]['EXTEND'].pop(__BASEINIT__)
        scope[1][__BASEINIT__] = baseConstructor
    if len(scope[1]['EXTEND'].keys())>0:
        scope[1].update(scope[1]['EXTEND'])
        caninherit.update(scope[1]['EXTEND'])   
    if len(scope[1]['IMPL'].keys())>0:
        for interfaceName in scope[1]['IMPL'].keys():
            ERROR(1044, line=scope[1]['IMPL'][interfaceName][1][2][3], interface=interfaceName, cls=node[1])
        return  
    for decl in todel:
        node[3].remove(decl)
    if node[3]:
        node[3] = staticvars + node[3]
    else:
        node[3] = staticvars
    if not isInter:
        if not constructor:
            constructor = ['fundef',__INIT__,['funsig',None,None,node[4]],None]
            scopechain.append(scope)
            declfun(constructor)
            scopechain.pop()
            node[3].append(constructor)
        if len(initdef)>0 or len(init)>0:       
            if constructor[3]:
                constructor[3] = initdef + init + constructor[3]
            else:
                constructor[3] = initdef + init    
        if baseConstructor and baseConstructor[2][1] and len(baseConstructor[2][1])>0:
            if hasNoSuper(constructor[3]):
                ERROR(1203,line=node[4],basename=scope[1]['BASE'])    
        elif scope[1].get('BASE') and hasNoSuper(constructor[3]):
            if not constructor[3]:
                constructor[3] = [] 
            constructor[3].append(['call', 'super',[],node[4]])    
        caninherit[__BASEINIT__] = constructor    
    scope[1]['INHERIT'] = caninherit   
    scope[1].pop('EXTEND')
    scope[1].pop('IMPL')    
    
def genNode(node,loop=False,assign=False):
    global outcode,scopechain,globalindex,localindex,funcPC2Name,debug

    print "*    ", node,'\n'
    
    if node[0] == 'vardef':#['vardef', 'const', [['varbind', ['typeid', 'b', ['int']], None]]]        
        
        cnt = 0
        for n in node[2]:            
            argType = ''
            if len(n[1]) > 3:
                argType = n[1][3]
                
            glTranslator.varDefBegin(n[1][1], argType, cnt)
            
            value = scopechain[-1][1].get(n[1][1])
            if value:
                ERROR(1151,line=node[3],name=n[1][1])
                return
            n[0] = node[1]
            if scopechain[-1][0] == 'g':                
                scopechain[-1][1][n[1][1]]=[globalindex,n]            
                globalindex += 1
            else:
                scopechain[-1][1][n[1][1]]=[-localindex-1,n]            
                localindex += 1
            if n[2]:
                if n[0]=='const':
                    constsMap[n[1][1]]=n[2][1] 
                genNode(n[2])
                index = scopechain[-1][1][n[1][1]][0]
                pc2line.append([len(outcode),node[3]])
                if -128<=index<=127:
                    outcode += chr(55)+pack('b',index)
                else:
                    outcode += chr(27)+pack('h',index)
            else:
                glTranslator.nullConstant()
                                        
            glTranslator.varDefEnd()
            cnt += 1
            
    elif node[0] == 'fundef':#['fundef', 'f', ['funsig',], None]
        glTranslator.beginMethod(node)

        pc2line.append([len(outcode),node[2][3]])
        outcode += chr(38)+pack('b',0)
        jump = [(38,len(outcode)-1,len(outcode))]
        make = scopechain[-1][1][node[1]][3]
        funcPC = len(outcode)
        funcpos = len(outcode)-make-5
        outcode = outcode[:make+1] + pack('i',funcpos)+ outcode[make+5:]        
        origIndex = localindex
        localindex = 0
        incls = None
        if node[2][1]:
            arglen = len(node[2][1])
        else:
            arglen = 0
        if type(scopechain[-1][0]) is int:
            arglen += 1
            localindex += 1
            incls = 1
        start = 0
        scopechain.append(('f',{},scopechain[-1][1][node[1]]))
        if node[2][1]:
            for arg in node[2][1]:
                if arg[0]=='...':
                    scopechain[-1][1][arg[1]] = [-localindex-1,arg]
                else:
                    if len(arg)==3:
                        start = 1
                    if start and len(arg) == 1:
                        ERROR(1138,line=node[2][3])
                    scopechain[-1][1][arg[0][1]] = [-localindex-1,arg]
                localindex += 1        
        if node[3]:
            for n in node[3]:
                if n[0]=='fundef':declfun(n)
            genNode(node[3])
        if not node[3] or node[3][-1][0]!='ret':
            #genNode(['ret',None,None])
            glTranslator.emptyRet(node)
            
        localindex = origIndex
        if fill(jump):
            outcode = outcode[:make+1] + pack('i',funcpos+1)+ outcode[make+5:]
            funcPC += 1
        scope = scopechain.pop()
        if debug:
            if incls:
                ele = ['this']*(len(scope[1].keys())+1)
            else:
                ele = ['0']*len(scope[1].keys())
            for key in scope[1].keys():                
                ele[-scope[1].get(key)[0]-1] = key
            funcname = node[1]
            if funcname == 0: funcname = scopechain[-1][0]
            funcPC2Name.append([funcPC,funcname,ele])  
        scopechain[-1][1][node[1]][2] = scope
        
        glTranslator.endMethod(node)
        
    elif node[0] == 'clsdef':        
        if scopechain[-1][0] != 'g':           
            ERROR(1131,line=node[4])
            return
        if node[3]:
            scopechain.append(scopechain[-1][1][node[1]][1])           
            glTranslator.beginClass(node)
            genNode(node[3])
            glTranslator.endClass(node)
            scopechain.pop()    
    elif node[0] == 'new':#['new', ['id', 'f'], [[],[]]]
        glTranslator.newObjectBegin(node[1][1])    
        
        for i in range(len(node[2])):                    
            glTranslator.newObjectArgument(i)
            genNode(node[2][i])
                
        glTranslator.newObjectEnd()                
        
    elif node[0] == 'call':#['call', ['id', 'f'], [[],[]]]
        sig = None
        if node[1] == 'super':
            ret = isInCls()
            if not ret[0] or ret[1]:
                ERROR(1006,line=node[3])
                return
            key = funcs.index(str(ret[0][2]-1)+'__INIT__')            
            pc2line.append([len(outcode),node[3]])
            outcode += chr(54)+pack('b',-1)
            pc2line.append([len(outcode),node[3]])
            if key <256:
                outcode += chr(71)+pack('B',key)
            else:
                outcode += chr(66)+pack('H',key)
            sig = getInBaseClass(ret[0],__INIT__)
        elif node[1][1] in internals or node[1][0] in internals:
            if node[1][0] == 'id':
                if findInScopeChain(node[1][1]):
                   ERROR(998,line=node[1][2],name=node[1][1])
                   return
                key = internals.index(node[1][1])
            else:
                key = internals.index(node[1][0])
            for arg in node[2]:
                genNode(arg)
            pc2line.append([len(outcode),node[3]])
            if key<256:
                outcode += chr(46)+pack('B',key)+pack('b',len(node[2]))
            else:
                outcode += chr(70)+pack('H',key)+pack('b',len(node[2]))
            if len(node)==5:
                outcode += chr(1)
            return
        elif node[1][0] == 'id' and node[1][1] == 'trace':
            for arg in node[2]:
                genNode(arg)
            pc2line.append([len(outcode),node[3]])
            outcode += chr(23)+pack('b',len(node[2]))
            return
        elif node[1][0] == 'id' and node[1][1] == 'substring':            
            for arg in node[2]:
                genNode(arg)
            pc2line.append([len(outcode),node[1][2]])
            if len(node[2])==2:
                outcode += chr(20)
            else:
                outcode += chr(22)
            return
        elif node[1][0] == 'id' and node[1][1] == 'Array':
            if len(node[2])>1:                
                genNode(['array',node[2],node[3]])
            elif len(node[2])==1:                
                if(node[2][0][0]=='id'):
                    r = int(constsMap[node[2][0][1]])
                else:
                    r = int(node[2][0][1])
                for i in range(r):
                    genNode(['i',0,node[1][2]])
                pc2line.append([len(outcode),node[3]])                
                outcode += chr(33)+pack('h',r) 
            else:
                pc2line.append([len(outcode),node[3]])                
                outcode += chr(33)+pack('h',0)
            return
        else:
            glTranslator.methodCallBegin()    
            sig = genNode(node[1])       
            
        argshort = False
        needArray = False
        size = 0
        if sig:
            if not sig[1]:                
                if len(node[2])>0:                   
                    ERROR(1136,line=node[3],num=0)
                    return
            else:
                size = len(sig[1])
                for i in range(len(sig[1])):                    
                    #print node
                    if i>=len(node[2]):
                        argshort = True
                        break
                    if sig[1][i][0]=='...':
                        needArray = True
                        break
                           
                    glTranslator.methodCallArgument(i)
                    genNode(node[2][i])
                
                glTranslator.methodCallEnd(
                                           )                
                if argshort:
                    while i<len(sig[1]) and len(sig[1][i])==2:
                        genNode(sig[1][i][1])       
                        i += 1            
                    if i < len(sig[1]):                    
                        ERROR(1136,line=node[3],num=len(sig[1]))
                        return
                if needArray:            
                    for exp in node[2][i:]:
                        genNode(exp)
                    pc2line.append([len(outcode),node[3]])                    
                    outcode += chr(33)+pack('h',len(node[2])-i)
                elif i<len(node[2])-1:                
                    ERROR(1136,line=node[3],num=len(sig[1]))
                    return
        else:
            size = len(node[2])
            for arg in node[2]:
                genNode(arg)
        pc2line.append([len(outcode),node[3]])       
        outcode += chr(47) + pack('b', size)
        if node[1] == 'super' or len(node)==5:
            outcode += chr(1)
    elif node[0] == 'super':
        ERROR(1006,line=node[2])
        return     
    elif node[0] == 'ret':
        glTranslator.retBegin()
        
        if node[1]:
            genNode(node[1][-1])
        else:
            node[2] = pc2line[-1][1]
            #genNode(['i',0,node[2]])   
            genNode(['null'])
        pc2line.append([len(outcode),node[2]])
        outcode += chr(24)
        
        glTranslator.retEnd()
    elif node[0] == 'id': #['id', 'a']
        ret = findInScopeChain(node[1])
        if not ret:
            if defines.get(node[1]) is not None:
                genNode(['i',defines[node[1]],node[2]])
            else:
                ERROR(1120,line=node[2],name=node[1])
            return
        scopeid = ret[0]
        value = ret[1]  
        if value[1][0] == 'const':            
            if assign and not inConstructor():
                ERROR(1049,line=node[2],name=node[1])
                return            
            if not assign:    
                #print node,'###',value 
                value[1][2][-1] = node[2]
                genNode(value[1][2])
                return
        if type(scopeid) is int:           
            if 'static' in value[0]:
                glTranslator.staticMemberId(node[1])
                
                pc2line.append([len(outcode),node[2]])
                if -128<=scopeid<=127:                   
                   outcode += chr(54)+pack('b',scopeid)
                else:
                   outcode += chr(32)+pack('h',scopeid)
            else:                                
                pc2line.append([len(outcode),node[2]])
                outcode += chr(54)+pack('b',-1)            
            if node[1] not in funcs:                 
                funcs.append(node[1])            
            key = funcs.index(node[1])
            if not assign:                
                pc2line.append([len(outcode),node[2]])
                if key < 256:
                    outcode += chr(71) + pack('B', key)
                else:
                    outcode += chr(66) + pack('H', key)
                if value[1][0] == 'fundef':                
                    glTranslator.memberFunctionId(node[1])
                    return value[1][2]
                elif 'static' not in value[0]:
                    glTranslator.memberId(node[1])
            else:
                glTranslator.memberId(node[1])
                return (1,key)
        elif not assign:            
            pc2line.append([len(outcode),node[2]])
            if -128<=value[0]<=127:
                outcode += chr(54)+pack('b',value[0])
            else:
                outcode += chr(32)+pack('h',value[0])
            if value[1][0] == 'fundef':                
                glTranslator.memberFunctionId(node[1])
                return value[1][2]        
            elif type(value[1][0]) is int and value[1][1].get(__INIT__):            
                glTranslator.localId(node[1])
                return value[1][1][__INIT__][1][2]
            else:
                glTranslator.localId(node[1])
        else:
            glTranslator.localId(node[1])
            return (0,value[0])
    elif node[0] == 'access':#['access', ['id', 'a'], ['[', [['i', '0']]] ]  #['access', ['this'], ['.', ['id', 'a']]]
        if node[2][0] == '[':
            if len(node[2][1])!=1:            
                ERROR(999,line=node[1][2], name=node[1][1])
                return
            else:
                genNode(node[1])            
                genNode(node[2][1][0])
                #print node
                if not assign:                       
                    pc2line.append([len(outcode),node[1][-1]])
                    outcode += chr(13)
        else:
            ex = False
            if node[1][0] == 'this':                
                ret = isInCls()
                if not ret[0] or ret[1]:
                    ERROR(1042,line=node[1][1])
                    return
                value = ret[0][1].get(node[2][1][1])
                if not value:
                    ERROR(1119,line=node[1][1],name=node[2][1][1])
                    return

                glTranslator.memberId(node[2][1][1])
                
                if 'static' in value[0]:
                    pc2line.append([len(outcode),node[1][1]])
                    if -128<=ret[0][0]<=127:
                       outcode += chr(54)+pack('b',ret[0][0])
                    else:
                       outcode += chr(32)+pack('h',ret[0][0])
                else:
                    pc2line.append([len(outcode),node[1][1]])
                    outcode += chr(54)+pack('b',-1)
            elif node[1][0] == 'super':
                ret = isInCls()
                if not ret[0] or ret[1]:
                    ERROR(1006,line=node[1][2])
                    return
                fname = node[2][1][1]
                if not ret[0][1].get(fname): 
                    ERROR(1119, line=node[1][2], name=node[2][1][1])
                    return
                if 'override' not in ret[0][1].get(fname)[0]:
                    node[1]=['this']                    
                    genNode(node)                    
                else:
                    pc2line.append([len(outcode),node[1][-1]])
                    outcode += chr(54)+pack('b',-1)                     
                    keyInBaseCls = funcs.index(str(ret[0][2]-1)+node[2][1][1])
                    pc2line.append([len(outcode),node[1][-1]])                    
                    if keyInBaseCls < 256:
                        outcode += chr(71) + pack('B', keyInBaseCls)
                    else:
                        outcode += chr(66) + pack('H', keyInBaseCls)     
                ex = True    
            else:
                genNode(node[1])            
            if not assign and not ex:
                if node[2][1][1] not in funcs: 
                    WARNING(0, line=node[2][1][-1], object=node[2][1][1])
                    funcs.append(node[2][1][1])
                key = funcs.index(node[2][1][1])                
                pc2line.append([len(outcode),node[2][1][-1]])                
                if key < 256:
                    outcode += chr(71) + pack('B', key)
                else:
                    outcode += chr(66) + pack('H', key)                     
    elif node[0] == 'assign':#['assign', '=', ['id', 'a'], ['biexp', '*', ['id', 'a'], ['i', '2']]]
       glTranslator.assignBegin()
       ret = genNode(node[2],loop,True)
       glTranslator.assignMiddle(node[1])
       genNode(node[3])
       glTranslator.assignEnd()
       
       #if not ret: return
       if node[2][0] == 'id':            
            if not ret: return
            if not ret[0]:
                pc2line.append([len(outcode),node[2][2]])
                if -128<=ret[1]<=127:
                    outcode += chr(55)+pack('b',ret[1])
                else:
                    outcode += chr(27)+pack('h',ret[1])
            else:
                pc2line.append([len(outcode),node[2][2]])                
                if ret[1] < 256:
                    outcode += chr(72) + pack('B', ret[1])
                else:
                    outcode += chr(67) + pack('H', ret[1])
       elif node[2][2][0] == '[':
           #print node
           pc2line.append([len(outcode),node[2][2][1][0][-1]])
           outcode += chr(51)
       else:
           if node[2][2][1][1] not in funcs: funcs.append(node[2][2][1][1])
           key = funcs.index(node[2][2][1][1])
           pc2line.append([len(outcode),node[4]])           
           if key < 256:
               outcode += chr(72) + pack('B', key)
           else:
               outcode += chr(67) + pack('H', key)    
    elif node[0] == 'uexp':
        if node[1] == '+':
            glTranslator.unOp(node[1])
            
            genNode(node[2])
        elif node[1] == '-':
            glTranslator.unOp(node[1])
            
            genNode(node[2])
        elif node[1] == '++':
            genNode(n)
            glTranslator.unOp(node[1])            
            return
        elif node[1] == '--':
            genNode(n)
            glTranslator.unOp(node[1])
            return
        elif node[1] == '~':
            print "Warning: ~ operator not supported"
        elif node[1] == '!':
            glTranslator.unOp(node[1])
            
            genNode(node[2])
        if node[-1]=='noret':
            outcode += chr(1)
    elif node[0] == 'uexpop':
        genNode(node[2])
        
        glTranslator.unOp(node[1])
                    
    elif node[0] == 'biexp':#['biexp', '*', ['i', '2'], ['i', '2']]        
        genNode(node[2])
        glTranslator.binOp(node[1])        
        genNode(node[3])            
    elif node[0] == 'i':        
        number = int(node[1])
        glTranslator.intConstant(number)
        
        number = int(node[1])        
        pc2line.append([len(outcode),node[2]])       
        if -128<=number<=127:
            outcode += chr(48)+pack('b',number)
        elif -32768<=number<=32767: 
            outcode += chr(39)+pack('h',number)
        else:
            outcode += chr(31)+pack('i',number)
    elif node[0] == 'f':
        number = float(node[1])		
        glTranslator.floatConstant(number)
        
        pc2line.append([len(outcode),node[2]])
        number2 = unpack('f', pack('f',number))
        percent = (number - number2[0])/number
        if abs(percent)>(1e-11):
            outcode += chr(77)+pack('d',number)
        else:
            outcode += chr(76)+pack('f', number)
    elif node[0] == 's':       
        glTranslator.stringConstant(node[1])
        
        s = eval(node[1])            
        pc2line.append([len(outcode),node[2]])
        outcode += chr(34)+pack('h',len(s))+s
    elif node[0] == 'array':
        for exp in node[1]:
            genNode(exp)        
        pc2line.append([len(outcode),node[2]])  
        outcode += chr(33)+pack('h',len(node[1]))
    elif node[0] == 'if':#['if', [['biexp',]], [['vardef', ],], ['if', [['biexp',], [['vardef', ],]],
        glTranslator.ifBegin()

        jump = []
        r1 = None
        r2 = None
        r = {}
        
        glTranslator.ifExpBegin()
        
        for exp in node[1]:
            genNode(exp)
            pc2line.append([len(outcode),node[4]])
            outcode += chr(37)+pack('h',0)
            jump.append((37,len(outcode)-2,len(outcode)))
        
        glTranslator.ifExpEnd()
                
        longjump = []
        if node[2]:
            if isinstance(node[2][0], types.ListType):            
                r1 = genNode(node[2],loop)        
            else:
                r1 = genNode([node[2]],loop)        
        if node[3]:
            pc2line.append([len(outcode),node[4]])
            outcode += chr(35)+pack('h',0)
        fill2(jump)
        
        isSingleStatement = False
        if node[3]:
            longjump.append((35,len(outcode)-2,len(outcode)))
            
            isSingleStatement = not (isinstance(node[3][0], types.ListType))
            glTranslator.ifElse(isSingleStatement)
            
            r2 = genNode(node[3],loop)         
            fill2(longjump)
        
        glTranslator.ifEnd(isSingleStatement)    
        
        if r1:
            r = r1
        if r2:
            if not r.get('b'):
                r['b'] = []
            r['b'] += r2['b']
            if not r.get('c'):
                r['c'] = []
            r['c'] += r2['c']
        if len(r.keys()):
            return r
    elif node[0] == 'do': 
        addr = len(outcode)
        con_br = None
        if node[1]:
            con_br = genNode(node[1],True)
            if con_br:
                fill2(con_br['c'])
        jump = []
        backjump = []
        for exp in node[2][:-1]:
            genNode(exp)
            pc2line.append([len(outcode),node[3]])
            outcode += chr(50)+pack('b',0)
            jump.append((50,len(outcode)-1,len(outcode)))
        genNode(node[2][-1])
        pc2line.append([len(outcode),node[3]])
        outcode += chr(36)+pack('h',0)
        fill(jump)
        backjump.append((36,len(outcode)-2,len(outcode)))
        fill2(backjump,addr)
        if con_br:
            fill2(con_br['b'])                
    elif node[0] == 'while':        
        glTranslator.whileBegin()
        
        for exp in node[1]:
            genNode(exp)
            
        glTranslator.whileBlock()
        if node[2]:
            if isinstance(node[2][0], types.ListType):            
                r1 = genNode(node[2],True)        
            else:
                r1 = genNode([node[2]],True)        
            
        glTranslator.whileEnd()
    elif node[0] == 'for':
        glTranslator.forBegin()
        
        if node[1]:
            genNode(node[1])
        
        glTranslator.forCondition()
        
        if node[2]:
            for exp in node[2]:
                genNode(exp)

        glTranslator.forStep()
        
        if node[3]:
            genNode(node[3][0])
        
        glTranslator.forBlock()
        
        if node[4]:
            if isinstance(node[4][0], types.ListType):            
                r1 = genNode(node[4],True)        
            else:
                r1 = genNode([node[4]],True)        
            
        glTranslator.forEnd()
        
    elif node[0] == 'continue':
        if not loop:
            ERROR(1039,line=node[1])
            
        glTranslator.continueStmt()
        
        pc2line.append([len(outcode),node[1]])
        outcode += chr(35)+pack('h',0)
        return ({'b':[],'c':[(35,len(outcode)-2,len(outcode))]})
    elif node[0] == 'break':
        if not loop:
            ERROR(1038,line=node[1])
        
        glTranslator.breakStmt()
        
        pc2line.append([len(outcode),node[1]])
        outcode += chr(35)+pack('h',0)
        return ({'b':[(35,len(outcode)-2,len(outcode))],'c':[]})
    elif node[0] == 'imp':
        pass
    elif node[0] == 'null':        
        outcode += chr(54)+pack('b',0)
        glTranslator.nullConstant()
        
    elif node[0] == 'this':
        ret = isInCls()
        if not ret[0] or ret[1]:
            ERROR(1042,line=node[1])
            return            
        pc2line.append([len(outcode),node[1]])
        outcode += chr(54)+pack('b',-1)
    elif type(node[0]) is str:        
        ERROR(0,name=node[0])
    else:
        r = {}
        for n in node:
            glTranslator.statementBegin()
            cb = genNode(n,loop)
            glTranslator.statementEnd()
                        
            if type(cb) is dict:
                if not r.get('b'):
                    r['b'] = []
                r['b'] += cb['b']
                if not r.get('c'):
                    r['c'] = []
                r['c'] += cb['c']
        if len(r.keys()):
            return r       
    return None

def getData(fdir):
    global queue    
    files = os.listdir(fdir)    
    for f in files:        
        if os.path.isdir(fdir+f):            
            getData(fdir+f+'/')                           
        elif f.endswith('.as'):
            print 'Parsing file : %s'%(fdir+f)
            data = open(fdir+f).read()
            p = asyacc.parse(data)
            p.append(fdir+f)
            queue.append(p)            

def link(direct):
    global queue, names, currentDir, prog    
    if direct[0] == 'pkg':    
        if not direct[2]: return []
        newdirects = []
        for d in direct[2]:
            newdirects += link(d)
        return newdirects
    elif direct[0] == 'prog':
        if not direct[1]: return []
        newdirects = []
        for d in direct[1]:
            newdirects += link(d)
        return newdirects
    elif direct[0] == 'imp':        
        if direct[1] in names: return []
        pkgs = direct[1].split('.')
        prefix = ''       
        for i in range(len(pkgs)-1):
            prefix += '.'+pkgs[i]+'.*'
            if prefix in names: return []               
        names.add(direct[1])
        fdir = direct[1].replace('.',os.sep)
        try:                
            if fdir[-2:]==os.sep+'*':
                getData(currentDir+fdir[:-1])                    
            else:
                print 'Parsing file : %s'%(currentDir+fdir+'.as')
                data = open(currentDir+fdir+'.as').read()
                p = asyacc.parse(data)
                p.append(currentDir+fdir+'.as')
                queue.append(p)
        except Exception, err:            
            print err
            ERROR(1172,name=direct[1],line=direct[2])
        return []  
    return [direct]

def decl(prog):
    global scopechain, globalindex, outcode, pc2line,funcPC2Name
    
    glTranslator.checkTypes(prog)
    
    scopechain.append(('g',{'null':0}))    
    globalindex += 1
    #outcode += pack('h',0)
    for node in prog:
        print 'Analyzing file : %s'%(node[2])
        pc2line.append(node[2])
        funs = []
        clses = []
        interfaces = []
        others = []
        for direct in node[1]:
            if direct[0]=='fundef':
                funs.append(direct)
            elif direct[0]=='clsdef':                
                clses.append(direct)
            elif direct[0]=='interface':
                interfaces.append(direct)
            else:
                others.append(direct)
        for direct in funs:
            declfun(direct)
        for direct in interfaces:
            declcls(direct, True)
        for direct in clses:
            declcls(direct)        
        for inter in interfaces:
            node[1].remove(inter)
    for node in prog:
        print 'Generating file : %s'%(node[2])
        
        glTranslator.beginFile(node[2])
        
        pc2line.append(node[2])
        for direct in node[1]:
            genNode(direct)
    outcode += chr(0)
    u = ''
    for i in range(len(extern)):
        fname = extern[i]
        u += pack('h',len(fname))+fname+pack('h',exFuncIndex[extern[i]])
    outcode = pack('h',len(extern))+u+outcode
    toadd = 2+len(u)
    for tag in pc2line:
        if type(tag) is not str:
            tag[0] += toadd
    for tag in funcPC2Name:
        tag[0] += toadd
        
def compile(argv):
    global errno,names,queue,prog,currentDir,funcPC2Name,debug
    try:
        optlist,args = getopt.getopt(argv,'o:',['PC=','output=','debug='])    
    except getopt.GetoptError,err:
        return False    
    if not args:
        print 'Please specify the input file'
        return False   
    fname = args[0]   
    outfile = fname[:fname.index('.')]
    debugfile = fname[:fname.index('.')]+'.debug'
    PC = 0   
    for o,aa in optlist:
        if o=='-o':
            outname = aa
        if o=='--output':
            outname = aa
        if o=='--PC':
            PC = int(aa)   
        if o=='--debug':
            debug = int(aa)    
    if PC:       
        f = open(debugfile)
        curfile = None
        lastnum = -1
        for line in f:                     
            if len(line.split())==1:
                curfile = line   
            else:
                curnum = int(line.split()[0])
                if PC > curnum:
                    lastnum = line.split()[1]
                elif PC == curnum:
                    print curfile, 'Error in line: ',line.split()[1]
                    sys.exit(0)
                elif PC < curnum:
                    print curfile, 'Error in line: ',lastnum
                    sys.exit(0)
        print curfile, 'Error in line: ',lastnum
        sys.exit(0)
    data = open(fname).read()
    currentDir = fname[:fname.rfind(os.sep)+1]
    funcname = fname.replace('.as','.func')
    print 'Parsing file : %s'%(fname)
    prog = asyacc.parse(data)
    prog.append(fname)
    names = set()
    queue = [list(prog)]
    prog = []
    while len(queue)>0:    
        subprog = queue.pop(0)
        directs = []
        for direct in subprog[1]:        
            directs += link(direct)
        subprog[1] = directs
        prog = [subprog]+prog
    #for p in prog:print p
    #try:
    decl(prog)
    #except Exception, err:
     #   errno = 1
      #  print err
    if errno==0:  
        fout = open(outfile,'wb')
        fout.write(outcode)
        fout.close()
        fout = open(debugfile,'w')
        for tag in pc2line:
            if type(tag) is str:
                fout.write(tag+'\n')
            else:
                fout.write(str(tag[0])+' '+str(tag[1])+'\n')
        fout.close()
        #print scopechain
        if debug:
            scope = scopechain[0][1]                 
            ele = ['0']*len(scope.keys())
            for key in scope.keys():
                v = scope.get(key)
                if type(v) is not int:
                    ele[v[0]]=key
            fout = open(funcname,'w')
            for func in funcs:
                fout.write(func+'\n')
            #print funcPC2Name
            for tag in funcPC2Name:
                to2 = tag[1]
                if type(to2) is int: to2 = ele[to2]                
                fout.write(str(tag[0])+' '+to2+'\n')
                fout.write(' '.join(tag[2])+'\n')
            fout.write('__g__ \n')            
            fout.write(' '.join(ele)+'\n')
            fout.close()
    return errno==0
    
if __name__=="__main__":
    compile(sys.argv)           
        
        
