from struct import pack,unpack
import re,sys,getopt,traceback,os

VER = 1
#k1 = re.compile("((?:.+\.)?[a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$")
#k2 = re.compile("([a-zA-Z_][a-zA-Z0-9_]*)\ *=(.*)$")
k3 = re.compile("([a-zA-Z_][a-zA-Z0-9_]*)$")
k4 = re.compile("if\ +(.+?)\:(.*)$",re.I)
k5 = re.compile("else\ *:(.*)$",re.I)
k6 = re.compile("elif\ +(.+?)\:(.*)$",re.I)
k7 = re.compile("while\ +(.+?)\:(.*)$",re.I)
#k9 = re.compile("(.*)\.([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$")
k10 = re.compile("for\ +([a-zA-Z_][a-zA-Z0-9_]*(?: *, *[a-zA-Z_][a-zA-Z0-9_]*)*,?)\ +in\ (.+)\:(.*)$",re.I)
k11 = re.compile("def\ +([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)\ *\:(.*)$",re.I)
k12 = re.compile("return\ +(.*)$",re.I)
k13 = re.compile("class\ +([a-zA-Z_][a-zA-Z0-9_]*)\ *(\([^()]*\))?\ *\:(.*)$",re.I)
re_int = re.compile('^[+-]*\d+$')
re_hex = re.compile('0[xX][0-9a-fA-F]+$')
re_float = re.compile('^[+-]*\d+\.\d*([eE][+-]?\d+)?$')
#funcs = filter(lambda a:not a.strip().startswith('#') and a,open('data\\funcs','r').read().split('\n'))
funcs = filter(lambda a:not a.strip().startswith('#') and a,open(os.path.join('data','funcs'),'rb').read().split('\r\n'))
funcs = map(lambda a: a.split('#')[0].strip(), funcs)
if len(funcs) != len(set(funcs)):
    print 'duplicated funcs declaration:'
    funcs_set = set(funcs)
    for i in funcs:
        if i not in funcs_set: print i
        else: funcs_set.discard(i)
else:
    #print len(funcs), 'global funcs'
    pass
ops = ('<=','>=','<','>','==','!=','<>','+','-','*','/','%','<<',
       '>>','|','&','^')
ops2 = (42,43,40,41,44,45,45,11,12,8,9,10,14,15,17,16,18)
filepath = None
compileok = True
included = []
debug = 1
funcPC2Name = []

def par(s,c1,c2):
    if s[0]!=c1 or s[-1]!=c2:
        return False
    j = k = 0
    j2 = j3 = 0
    for i in range(len(s)):
        if j2:
            if s[i]=="'": j2=0
            continue
        if j3:
            if s[i]=='"': j3=0
            continue
        if s[i]==c2 and (c1!=c2 or j>0): j-=1
        elif s[i]==c1: j+=1
        if s[i]=="'" and c1!="'" and c1!='"': j2=1
        if s[i]=='"' and c1!='"' and c1!="'": j3=1
        if j==0:
            return i==len(s)-1
    return False

def split(s,c,maxsplit=0):
    r = []
    r2 = []
    j = j2 = j3 = j4 = k = 0
    for i in range(len(s)):
        if j2:
            if j4:
                j4 = 0
                continue
            if s[i]=="\\": j4=1
            if s[i]=="'": j2=0
            continue
        if j3:
            if j4:
                j4 = 0
                continue
            if s[i]=="\\": j4=1
            if s[i]=='"': j3=0
            continue
        if s[i]=='(': j+=1
        if s[i]==')': j-=1
        if s[i]=='[': j+=1
        if s[i]==']': j-=1
        if s[i]=='{': j+=1
        if s[i]=='}': j-=1
        if s[i]=="'": j2=1
        if s[i]=='"': j3=1
        if j==0:
            if s[k:i].strip().startswith('lambda ') and s[k:i].find(':')==-1:
                continue
            for l in range(len(c)):
                if s[i:i+len(c[l])]==c[l]:
                    if len(c[l])==1 and (i>0 and s[i-1]==c[l] or i<len(s)-1 and s[i+1]==c[l]): continue
                    if c[l]=='=' and (i>0 and (s[i-1]=='>' or s[i-1]=='<' or s[i-1]=='!' or s[i-1]=='=') or i<len(s)-1 and s[i+1]=='='): continue
                    r.append(s[k:i])
                    r2.append(l)
                    k=i+len(c[l])
                    break
            if maxsplit>0 and k<len(s) and len(r)>=maxsplit:
                break
    if k<len(s):
        r.append(s[k:])
    return (r,r2)

def fill(w,k,t,d=None):
    global outcode
    global line2code
    smaller = {35:38,36:49,37:50,52:53,25:2,26:3,60:61}
    if t:
        if -128<=k-w<=127:
            if ord(outcode[w-3]) not in smaller:
                print 'Error fill in ',w-3
                return -1
            outcode = outcode[:w-3]+chr(smaller[ord(outcode[w-3])])+pack('b',k-w)+outcode[w:]
            for i in jump:
                if i[0]>=w: i[0]-=1
                if i[1]>=w: i[1]-=1
#            for i in funcpos:
#                if funcpos[i]>=w:
#                    funcpos[i]-=1
            if debug: 
                for i in funcPC2Name:
                    if i[0]>=w : i[0]-=1
            for i in range(len(line2code)):
                if line2code[i]>=w:
                    line2code[i]-=1
            return 1
        else:
            return 0
    else:
        if d:
            outcode = outcode[:w-1]+pack('b',k-w)+outcode[w:]
        else:
            outcode = outcode[:w-2]+pack('h',k-w)+outcode[w:]


def push(s):
    global outcode,loc,lines,compileok,lineinfo,inf
    s = s.strip()
    if par(s,'(',')'):
        t = split(s[1:-1],[','])[0]
        if len(t)>1:
            print "Warning: tuple (...) isn't supported. Use [...] instead."
            for j in t: push(j)
            outcode+=chr(33)+pack('h',len(t))
            return len(t)
    while par(s,'(',')'):
        s=s[1:-1].strip()
    if par(s,'[',']'):
        t = split(s[1:-1],[' for '],1)[0]
        if len(t)==2:
            t2 = split(t[1],[' if '],1)[0]
            ifs = None
            if len(t2)==2:
                t[1],ifs = t2
            t3 = split(t[1],[' in '],1)[0]
            loc.append('temp')
            temp = len(loc)-1
            temp = -temp-1
            outcode += chr(33)+pack('h',0)
            if -128<=temp<=127:
                outcode += chr(55)+pack('b',temp)
            else:
                outcode += chr(27)+pack('h',temp)
            push(t3[1])
            outcode += chr(59)
            p1 = len(outcode)
            outcode += chr(60)+'XX'
            p2 = len(outcode)

            x = t3[0].strip().split(',')
            if len(x)>1:
                if x[-1]=='': x.pop(-1)
                x.reverse()
                outcode+=chr(29)+pack('h',len(x))
                for j in x: pop(j)
            else:
                pop(x[0])
            if ifs:
                push(ifs)
                outcode += chr(37)+'XX'
                p3 = len(outcode)
            else:
                p3 = 0
                
            if -128<=temp<=127:
                outcode += chr(54)+pack('b',temp)
            else:
                outcode += chr(32)+pack('h',temp)
            push(t[0])
            outcode += chr(46)+pack('B',funcs.index('append'))+chr(2)
            outcode += chr(1)
            
            p4 = len(outcode)
            outcode += chr(35)+'XX'
            p5 = len(outcode)
            outcode += chr(62)

            if -128<=temp<=127:
                outcode += chr(54)+pack('b',temp)
            else:
                outcode += chr(32)+pack('h',temp)

            jump.append([p2,p5])
            if p3: jump.append([p3,p4])
            jump.append([p5,p1])
            
            return 0
        else:
            t = split(s[1:-1],[','])[0]
            for j in t: push(j)
            outcode+=chr(33)+pack('h',len(t))
            return len(t)
    if par(s,'{','}'):
        t = split(s[1:-1],[','])[0]
        if t and len(split(t[0],[':'])[0])<=1:
            for j in t: push(j)
            outcode+=chr(33)+pack('h',len(t))
            outcode+=chr(46)+pack('B',funcs.index('set'))+chr(1)
        elif t:
            for j in t:
                x = split(j,[':'])[0]
                if len(x)!=2:
                    print 'Error5 in %s:\nNot a dict element: %s'%(lineinfo[lines],j)
                    compileok = False
                    return
                for k in x:
                    push(k)
                outcode+=chr(33)+pack('h',2)
            outcode+=chr(33)+pack('h',len(t))
            outcode+=chr(46)+pack('B',funcs.index('dict'))+chr(1)
        else:
            outcode+=chr(46)+pack('B',funcs.index('dict'))+chr(0)
        return len(t)
        
    #if s in defines: s = defines[s]
    if s in defines: return push(defines[s])

        
#    if s in funcs:
#        s = 'lambda x:'+s+'(x)'
        
    if s.startswith('lambda ') or s.startswith('lambda:'):
        outcode += chr(52)+'XX'
        uk = len(outcode)
        jump.append([uk,uk+3])
        outcode += chr(35)+'XX'
        u = s[6:s.find(':')].strip()
        loc0 = loc
        loc = []
        for uu in split(u,',')[0]:
            loc.append(uu.strip())
        post.append([-1,3])
        inf += 1
        push(s[s.find(':')+1:])
        inf -= 1
        post.pop(-1)
        outcode += chr(24)
        jump.append([uk+3,len(outcode)])
        loc = loc0
        return 0

    j = split(s,[' or '])[0]
    if len(j)>1:
        l = []
        for k in range(len(j)):
            push(j[k])
            if k!=len(j)-1:
                outcode += chr(25)+'XX'
                l.append(len(outcode))
                outcode += chr(1)
#        outcode += chr(48)+chr(0)+chr(38)+pack('b',2)
        for k in l:
            jump.append([k,len(outcode)])
#        outcode += chr(48)+chr(1)
        return 0
                
    j = split(s,[' and '])[0]
    if len(j)>1:
        l = []
        for k in range(len(j)):
            push(j[k])
            if k!=len(j)-1:
                outcode += chr(26)+'XX'
                l.append(len(outcode))
                outcode += chr(1)
#        outcode += chr(48)+chr(1)+chr(38)+pack('b',2)
        for k in l:
            jump.append([k,len(outcode)])
#        outcode += chr(48)+chr(0)
        return 0
        
    j = split(s,[' not in '],1)[0]
    if len(j)==2:
        for k in j:
            push(k)
        outcode += chr(4)
        return 0
                
    j = split(s,[' in '],1)[0]
    if len(j)==2:
        for k in j:
            push(k)
        outcode += chr(5)
        return 0
                
    j = split(s,[' is not '],1)[0]
    if len(j)==2:
        for k in j:
            push(k)
        outcode += chr(63)
        return 0
                
    j = split(s,[' is '],1)[0]
    if len(j)==2:
        for k in j:
            push(k)
        outcode += chr(64)
        return 0
        
    # xxx if xxx else xxx
    j = split(s,[' if '],1)[0]
    if len(j)==2:
        k = split(j[1],[' else '],1)[0]
        if len(k)==2:
            l = []
            push(k[0])
            outcode += chr(37)+'XX'
            l.append(len(outcode))
            push(j[0])
            outcode += chr(35)+'XX'
            l.append(len(outcode))
            push(k[1])
            l.append(len(outcode))
            jump.append([l[0],l[1]])
            jump.append([l[1],l[2]])
            return 0
                
    j = split(s,ops[:7])
    if len(j[0])>2:
        s = ''
        for i in range(len(j[0])-1):
            s += j[0][i]+ops[j[1][i]]+j[0][i+1]
            if i<len(j[0])-2:
                s += ' and '
        return push(s)
    elif len(j[0])==2:
        push(j[0][0])
        push(j[0][1])
        outcode += chr(ops2[j[1][0]])
        return 0

    j = split(s,ops[7:9])
    if s[0]=='-':
        j[0].pop(0)
        j[0][0] = '-'+j[0][0]
        j[1].pop(0)
    if len(j[0])>=2:
        for k in range(len(j[0])):
            push(j[0][k])
            if k>0:
                outcode += chr(ops2[7+j[1][k-1]])
        return 0
    
    j = split(s,ops[9:12])
    if len(j[0])>=2:
        for k in range(len(j[0])):
            push(j[0][k])
            if k>0:
                outcode += chr(ops2[9+j[1][k-1]])
        return 0
    
    for i in range(12,len(ops)):
        j = split(s,[ops[i]])[0]
        if len(j)>1:
            for k in range(len(j)):
                push(j[k])
                if k>0:
                    outcode += chr(ops2[i])
            return 0

    if s[0]=='-':
        push(s[1:])
        outcode+=chr(6)
        return 0
    if s[:4]=='not ':
        push(s[4:])
        outcode+=chr(7)
        return 0

    if s[-1]==']' and len(s)>2:
        for i in range(len(s)-2,0,-1):
            if par(s[i:],'[',']'):
                push(s[:i])
                u = s[i+1:-1]
                if u==':':
                    outcode += chr(19)
                elif u[-1]==':':
                    push(u[:-1])
                    outcode += chr(20)
                elif u[0]==':':
                    push(u[1:])
                    outcode += chr(21)
                elif len(split(u,':')[0])==2:
                    u2 = split(u,':')[0]
                    for i in u2: push(i)
                    outcode += chr(22)
                else:
                    push(u)
                    outcode += chr(13)
                return 0

    if par(s,"'","'") or par(s,'"','"') or len(s)>1 and s[0].upper()=='R' and (par(s[1:],"'","'") or par(s[1:],'"','"')):
        t = eval(s)
        if s[0].upper()!='R': t = t.decode('gbk').encode('utf8')
        outcode+=chr(34)+pack('h',len(t))+t
        return 0
    if re_int.match(s) or re_hex.match(s):
        if s.upper().startswith('0X'):
            t = int(s,16)
        else:
            t = int(s)
        if -128<=t<=127:
            outcode+=pack('bb',48,t)
        elif -32768<=t<=32767:
            outcode+=chr(39)+pack('h',t)
        else:
            outcode+=chr(31)+pack('i',t)
        return 0
    if re_float.match(s):
        t = float(s)
        t2 = unpack('f',pack('f',t))[0]
        if abs(t2-t)/t>1e-11:
            outcode+=chr(77)+pack('d',t)
        else:
            outcode+=chr(76)+pack('f',t)
        return 0

    if s[-1]==')' and len(s)>2:
        for i in range(len(s)-2,0,-1):
            if par(s[i:],'(',')'):
                x = s[i+1:-1]
                u = s[:i]
                if u.rfind('.')==-1 and u not in glo and u not in loc:
                    if u not in funcs:
                        print "line: %s  unknown symbol : %s"%(lineinfo[lines],u)
                        compileok = False
                        return 0
                    u2 = funcs.index(u)
                    if u2<256:
                        s2 = chr(46)+pack('B',u2)+pack('b',push('['+x+']'))
                    else:
                        s2 = chr(70)+pack('H',u2)+pack('b',push('['+x+']'))
                    outcode = outcode[:-3]+s2
                else:
                    push(u)
                    s2 = chr(47)+pack('b',push('['+x+']'))
                    outcode = outcode[:-3]+s2
                return 0

    inclass = None
    for i in reversed(post):
        if i[1]==5:
            inclass = i[2]
            break
        elif i[1]==3:
            break
    prefix = None
    if s.rfind('.')!=-1:
        prefix,s = s.rsplit('.',1)
    if k3.match(s):
        u = s        
        if prefix:
            pass
        elif u in loc:
            u2 = -loc.index(u)-1
            if inclass:
                prefix = inclass
        elif u in glo:
            u2 = glo.index(u)
        else:
            print "line: %s  unknown symbol : %s"%(lineinfo[lines],u)
            compileok = False
            return 0
            glo.append(u)
            if len(glo)>=1000:
                print "Too many globals"
            u2 = glo.index(u)
        if prefix:
            push(prefix)
            if u not in funcs:
                print 'Warning: line: %s  %s.%s not defined'%(lineinfo[lines],prefix,u)
                funcs.append(u)
            u2 = funcs.index(u)
            if u2<256:
                outcode += chr(71)+chr(u2)
            else:
                outcode += chr(66)+pack('H',u2)
        elif -128<=u2<=127:
            outcode += chr(54)+pack('b',u2)
        else:
            outcode += chr(32)+pack('h',u2)
        return 0
    print 'Error1 in %s:\n%s'%(lineinfo[lines],s)
    compileok = False


def pop(s):
    global outcode,compileok,lines,lineinfo
#    print s
    s = s.strip()
    while par(s,'(',')'):
        s=s[1:-1].strip()
    if par(s,'[',']'):
        t = split(s[1:-1],[','])[0]
        t.reverse()
        outcode+=chr(29)+pack('h',len(t))
        for j in t: pop(j)
        return len(t)

    if s[-1]==']' and len(s)>2:
        for i in range(len(s)-2,0,-1):
            if par(s[i:],'[',']'):
                push(s[:i])
                push(s[i+1:-1])
                outcode += chr(51)
                return 0

    inclass = None
    for i in reversed(post):
        if i[1]==5:
            inclass = i[2]
            break
        elif i[1]==3:
            break

    prefix = None
    if s.rfind('.')!=-1:
        prefix,s = s.rsplit('.',1)
    if k3.match(s):
        u = s       
        if prefix:
            u2 = 1
        elif inclass:
            if u not in loc:
                loc.append(u)
            u2 = 1
            prefix = inclass
        elif u in loc:
            u2 = -loc.index(u)-1
        elif (not inf or u in globals) and u in glo:
            u2 = glo.index(u)
        elif inf:
            if u in glo:
#                warning.append('Warning in line %d%s:\n%s\n%s exists in globals'%(lines,str(lineinfo[lines]),s,u))            
                print 'Error in %s:\n%s\n%s exists in globals'%(lineinfo[lines],s,u)
                compileok = False
                return
            loc.append(u)
            u2 = -loc.index(u)-1
        else:
            glo.append(u)
            if len(glo)>=1000:
                print "Too many globals"
            u2 = glo.index(u)
        if u2==0:
            print 'Assignment to None!'
            compileok = False
            return
        if prefix:
            push(prefix)
            if u not in funcs: funcs.append(u)
            u2 = funcs.index(u)
            if u2<256:
                outcode += chr(72)+chr(u2)
            else:
                outcode += chr(67)+pack('H',u2)
        elif -128<=u2<=127:
            outcode += chr(55)+pack('b',u2)
        else:
            outcode += chr(27)+pack('h',u2)
        return u2
    print 'Error2 in %s:\n%s'%(lineinfo[lines],s)
    compileok = False
    
def main(argv):
    global filepath,outcode,line2code,loc,globals,inf,compileok,lines,lineinfo
    try:
        optlist,args = getopt.getopt(argv, 'qdhpgi',['define=','output=','PC='])
    except getopt.GetoptError,err:
        return False
    if not args:
        print 'Please specify the input file'
        return False
    fname = args[0]
    filepath = os.path.split(fname)[0]
    outname = fname[:fname.index('.')]+'.vst'    
    infoname = fname[:fname.index('.')]+'.nfo'    

    global outcode,glo,loc,globals,post,jump,inf,funcpos,extern,defines,ifdefines,warning,funcPC2Name
    outcode = ""
    glo = ['None']
    loc = []
    globals = []
    post = []
    jump = []
    inf = 0
    funcpos = {}
    extern = ['initialize','start']
    defines = {}
    ifdefines = []
    warning = []

    ppp = quiet = disablep = enabledebug = infofile = False
    PC = 0
    for o,aa in optlist:
        if o=='-q': quiet = True
        if o=='-d': disablep = True
        if o=='-p': ppp = True
        if o=='-g': enabledebug = True
        if o=='-i': infofile = True
        if o=='--define':
            #todo
            dddd=aa
        if o=='--output':
            outname = aa
        if o=='--PC':
            PC = int(aa)
        if o=='-h': 
            return False

    if disablep:  print 'print disabled'            
    
    consts = open(os.path.join('data','const')).readlines()
    code = open(fname).readlines()
    lineinfo = []
    for i in range(len(consts)):
        lineinfo.append(('consts.py',i+1))
    for i in range(len(code)):
        lineinfo.append((fname,i+1))
        # chck for '\t'
        if '\t' in code[i]:
            print 'TAB(0x09) found at line', i+1,'!'
            return False
    code = consts+code
    indent = 0
    
    code.append('pass')
    lineinfo.append(('system',-1))
    lines = -1
    i0 = 0
    line2code = []
    line2 = []
    while i0<len(code):
        if enabledebug:
            outcode += chr(57)+'Dg'+lineinfo[lines][0]+':'+str(lineinfo[lines][1]+1)+':'+str(lines+1)+chr(0)
        lines += 1
    
        try:            
            line2code.append(len(outcode))
            i = code[i0]            
            line2.append(i)
            #print lineinfo[lines],i.rstrip()
            if i.strip()=='':
                i0 += 1
                continue
            if i.strip().startswith('#'):
                i = i.strip()
                if i.startswith('#define '):
                    i = i[8:].split()
                    if len(i)==1: defines[i[0]]=1
                    else: defines[i[0]] = i[1]
                elif i.startswith('#ifdef '):
                    ifdefines.append(i[7:].strip())
                elif i.startswith('#ifndef '):
                    ifdefines.append('!'+i[8:].strip())
                elif i.startswith('#else') and ifdefines:
                    ifdefines[-1] = '!'+ifdefines[-1]
                elif i.startswith('#endif'):
                    ifdefines.pop()
                elif i.startswith('#include '):
                    i = i[9:].strip()
                    if i[0]=='"' and i[-1]=='"': i = i[1:-1]
                    if i[0]=="'" and i[-1]=="'": i = i[1:-1]
                    fs = os.path.join(filepath,i)
                    if fs not in included:
                        included.append(fs)
                        o = open(fs).readlines()
                        code = code[:i0+1]+o+code[i0+1:]
                        oo = []
                        for j in range(len(o)):
                            oo.append([i,j+1])
                        lineinfo = lineinfo[:i0+1]+oo+lineinfo[i0+1:]
                i0 += 1
                continue
            i = split(i,'#')[0][0].rstrip()

            while i.endswith('\\') or i.endswith(','):
                j0 = i0+1
                while code[j0]=='': j0 += 1
                if i.endswith('\\'):
                    i = i[:-1]+code[j0].strip()
                else:
                    i += code[j0].strip()
                code[j0] = ''

            ok = False
            for j in ifdefines:
                if j.startswith('!') and j[1:] in defines or not j.startswith('!') and j not in defines:
                    ok = True
            if ok:
                i0 += 1
                continue
            if i.find(chr(9))!=-1:
                print "Please use SPACE instead of TAB in source code : %s"%(lineinfo[lines],)
                compileok = False
                break
            ii = 0
            while i[ii]==' ': ii+=1
            ii/=4
            i = i.strip()
            cont = False
            while (ii<indent):
                indent -= 1
                a = post[-1]
                if a[1]==1:
                    if a[0]==ii and k5.match(i):
                        t = k5.match(i)
                        outcode += chr(35)+'XX'
                        w = a.pop()
                        jump.append([w,len(outcode)])
                        a.append(len(outcode))
                        indent+=1
                        s = t.group(1).strip()
                        if len(s)>0:
                            code.insert(i0+1, ' '*4*indent+s)
                            lineinfo.insert(i0+1, (fname,lineinfo[i0][1]))
                        cont = True
                        break
                    elif a[0]==ii and k6.match(i):
                        t = k6.match(i)
                        outcode += chr(35)+'XX'
                        w = a.pop()
                        jump.append([w,len(outcode)])
                        a.append(len(outcode))
                        push(t.group(1))
                        outcode += chr(37)+'XX'
                        a.append(len(outcode))
                        indent+=1
                        s = t.group(2).strip()
                        if len(s)>0:
                            code.insert(i0+1, ' '*4*indent+s)
                            lineinfo.insert(i0+1, (fname,lineinfo[i0][1]))
                        cont = True
                        break
                    else:
                        for k in range(2,len(a)):
                            jump.append([a[k],len(outcode)])
                elif a[1]==2 or a[1]==4:
                    outcode += chr(35)+pack('h',a[2]-len(outcode)-3)
                    jump.append([len(outcode),a[2]])
                    for k in range(3,len(a)):
                        if a[k][0]==0:
                            jump.append([a[k][1],len(outcode)])
                        else:
                            jump.append([a[k][1],a[2]])
                    if a[1]==4:
                        outcode += chr(62)
                elif a[1]==3:
                    if debug: funcPC2Name[-1][2] = loc
                    outcode += chr(54)+chr(0)+chr(24) 
                    jump.append([a[2],len(outcode)])
                    inf -= 1
                    loc = a[3]
                    globals = a[4]
                elif a[1]==5:
                    loc = a[3]
                    globals = a[4]
                post.pop()
            line2code[-1]=len(outcode)
            if cont:
                i0 += 1
                continue
            if i=='pass':
                i0 += 1
                continue
            if i=='break':
                outcode += chr(35)+'XX'
                for i in range(len(post)-1,-1,-1):
                    if post[i][1]==2 or post[i][1]==4:
                        post[i].append([0,len(outcode)])
                        break
                i0 += 1
                continue
            if i=='continue':
                outcode += chr(35)+'XX'
                for i in range(len(post)-1,-1,-1):
                    if post[i][1]==2 or post[i][1]==4:
                        post[i].append([1,len(outcode)])
                        break
                i0 += 1
                continue
            if i.startswith('del '):
                for u in map(lambda x:x.strip(),split(i[4:].strip(),[','])[0]):
                    if u[-1]==']' and len(u)>2:
                        for i in range(len(u)-2,0,-1):
                            if par(u[i:],'[',']'):
                                push(u[:i])
                                push(u[i+1:-1])
                                outcode += chr(65)
                                break
                        continue
                    if u.rfind('.')!=-1:
                        prefix,u = u.rsplit('.',1)
                        push(prefix)
                        if u not in funcs: funcs.append(u)
                        u2 = funcs.index(u)
                        if u2<256:
                            outcode += chr(73)+chr(u2)
                        else:
                            outcode += chr(68)+pack('H',u2)
                        continue
                    if u in loc:
                        u2 = -loc.index(u)-1
                    else:
                        u2 = glo.index(u)
                    if -128<=u2<=127:
                        outcode += chr(56)+pack('b',u2)
                    else:
                        outcode += chr(28)+pack('h',u2)
                i0 += 1
                continue
            if i.startswith('print '):
                if disablep:
                    i0 += 1
                    continue
                i = push('['+i[6:]+']')
                outcode = outcode[:-3]
                outcode += chr(23)+pack('b',i)
                i0 += 1
                continue
            if i.startswith('extern '):
                s = i[7:].strip()
                extern.append(s)
                i0 += 1
                continue
            '''if i.endswith('++'):
                u = i[:-2].strip()
                if u in loc:
                    u2 = -loc.index(u)-1
                else:
                    print 'Error in line %d%s:\n%s\n%s exists in globals'%(lines,str(lineinfo[lines]),s,u)
                    compileok = False
                outcode += chr(58)+pack('b',u2)
                i0 += 1
                continue'''

            t = k11.match(i)
            if t:
                outcode += chr(52)+'XX'
                u3 = len(outcode)
                u2 = pop(t.group(1))
                jump.append([u3,len(outcode)+3])               
                u = t.group(2)
                outcode += chr(35)+'XX'                
                post.append([indent,3,len(outcode),loc,globals])
                if debug:  funcPC2Name.append([len(outcode),t.group(1),[]])
                loc = []
                globals = []
                defaults = []
                for uu in split(u,',')[0]:
                    if uu.find('=')!=-1:
                        uu,v = uu.split('=',1)
                        defaults.append((uu,v))
                    loc.append(uu.strip())                
                funcpos[t.group(1)] = u2 # len(outcode)
                indent += 1
                inf += 1
                i0 += 1
                for uu,v in defaults:
                    push(v)
                    outcode += chr(74)+chr(loc.index(uu.strip()))
                uu = t.group(3).strip()
                if len(uu)>0:
                    code.insert(i0,' '*4*indent+uu)
                    lineinfo.insert(i0,(fname,lineinfo[i0][1]))
                continue
                
            t = k12.match(i)
            if t:
                for i in reversed(post):
                    if i[1]==3: break
                    if i[1]==4:
                        outcode += chr(62)
                push(t.group(1))
                outcode += chr(24)
                i0 += 1
                continue
            if i.strip()=='return':
                for i in reversed(post):
                    if i[1]==3: break
                    if i[1]==4:
                        outcode += chr(62)
                push('None')
                outcode += chr(24)
                i0 += 1
                continue
            if i.strip().startswith('global '):
                globals.extend(map(lambda x:x.strip(),i.strip()[7:].strip().split(',')))
                i0 += 1
                continue
                
            t = k13.match(i)
            if t:
                supers = t.group(2)
                if supers and supers[0]=='(' and supers[-1]==')':
                    supers = split(supers[1:-1],[','])[0]
                    for i in supers:
                        push(i)
                    outcode += chr(69)+chr(len(supers))
                else:
                    outcode += chr(69)+chr(0)
                s = t.group(1).strip()
                pop(s)
                post.append([indent,5,s,loc,globals])
                loc = []
                globals = []
                indent += 1
                s = t.group(3).strip()
                if len(s)>0:
                    code.insert(i0+1, ' '*4*indent+s)
                    lineinfo.insert(i0+1,(fname,lineinfo[i0][1]))
                i0 += 1
                continue
            
            t = k4.match(i)
            if t:
                push(t.group(1))
                outcode += chr(37)+'XX'
                post.append([indent,1,len(outcode)])
                indent+=1
                s = t.group(2).strip()
                if len(s)>0:
                    code.insert(i0+1, ' '*4*indent+s)
                    lineinfo.insert(i0+1,(fname,lineinfo[i0][1]))
                i0 += 1
                continue
            t = k7.match(i)
            if t:
                p1 = len(outcode)
                push(t.group(1))
                outcode += chr(37)+'XX'
                post.append([indent,2,p1,(0,len(outcode))])
                indent+=1
                s = t.group(2).strip()
                if len(s)>0:
                    code.insert(i0+1, ' '*4*indent+s)
                    lineinfo.insert(i0+1,(fname,lineinfo[i0][1]))
                i0 += 1
                continue
            t = k10.match(i)
            if t:
                push(t.group(2))
                outcode += chr(59)
                p1 = len(outcode)
                outcode += chr(60)+'XX'
                post.append([indent,4,p1,(0,len(outcode))])
                x = t.group(1).strip().split(',')
                if len(x)>1:
                    if x[-1]=='': x.pop(-1)
                    x.reverse()
                    outcode+=chr(29)+pack('h',len(x))
                    for j in x: pop(j)
                else:
                    pop(x[0])
                indent+=1
                s = t.group(3).strip()
                if len(s)>0:
                    code.insert(i0+1, ' '*4*indent+s)
                    lineinfo.insert(i0+1,(fname,lineinfo[i0][1]))
                i0 += 1
                continue
    
            k = 0
            for j in range(7,len(ops)):
                t = split(i,[ops[j]+'='])[0]
                if len(t)==2:
                    push(t[0])
                    push(t[1])
                    outcode += chr(ops2[j])
                    pop(t[0])
                    k = 1
                    i0 += 1
                    break
            if k: continue
    
            t = split(i,['='])[0]
            if len(t)>=2:
                for k in range(len(t)-2,-1,-1):
                    if len(split(t[k+1],[','])[0])>1: push('['+t[k+1]+']')
                    else: push(t[k+1])
                    if len(split(t[k],[','])[0])>1: pop('['+t[k]+']')
                    else: pop(t[k])
                i0 += 1
                continue
            
            push(i)
            outcode = outcode+chr(1)
            i0 += 1
    
            #print 'Error3 in line %d%s:\n%s'%(lines,str(lineinfo[lines]),i)
            #compileok = False
            #i0 += 1
    
        except Exception,e:
            print 'Error4 in %s:\n%s'%(lineinfo[lines],i), e
            traceback.print_exc()
            compileok = False
            break
   
    outcode += chr(0)
    for i in range(len(jump)):
        t = fill(jump[i][0],jump[i][1],True)
        if t==-1:
            compileok = False
        jump[i].append(t)
    for i in range(len(jump)):
        fill(jump[i][0],jump[i][1],False,jump[i][2])
    u = ''
    k = 0   
    for i in range(len(extern)):
        if extern[i] in funcpos:
            j = extern[i]
            u += pack('h',len(j))+j+pack('h',funcpos[extern[i]])
            k += 1
    outcode = 'PPY'+pack('h',VER)+pack('h',k)+u+outcode+fname[:fname.index('.')]    
    
    if compileok:
        open(outname,'wb').write(outcode)
        if debug:
            fout = open(outname+'.func','w')
            for func in funcs:
                fout.write(func+'\n')
            for tag in funcPC2Name:
                fout.write(str(tag[0]+7+len(u))+' '+tag[1]+'\n')
                fout.write(' '.join(tag[2])+'\n')
            fout.write('__g__ \n')  
            fout.write(' '.join(glo)+'\n')
            
            fout = open(outname+'.debug','w')
            oldfname = ''
            for i in range(len(line2code)):
                if lineinfo[i][0]!=oldfname:
                    oldfname = lineinfo[i][0]
                    fout.write(oldfname+'\n')
                if i>=len(line2code)-1 or line2code[i]!=line2code[i+1]:
                    fout.write(str(line2code[i]+7+len(u)) + ' ' +str(lineinfo[i][1]) + '\n')
            fout.close()
            
    ppa = compileok and ppp and not quiet
    ppb = compileok and infofile
    if PC:
        print 'PC =',PC
        found = False
        for i in range(len(line2code)-1):
            if PC<=line2code[i]+2+len(u):
                print 'line =',lineinfo[i-1]
                print line2[i-1].strip('\n')
                found = True
                break
        if not found:
            print "Can't find line"
    if ppa or ppb:
        infos = ''
        for i in range(len(line2code)):
            msg = ' '.join(map(str,[i, ':' , line2code[i]+2+len(u),':',lineinfo[i],line2[i].strip('\n')]))
            infos+=msg+'\n'    
        if ppa: print infos
        if ppb: open(infoname,'w').write(infos)        
    if warning:
        print 'Warning:'
        for i in warning:
            print i
    else:
        if compileok and not ppp and not quiet:
            #print 'compile ok'
            pass   
    return compileok

if __name__=="__main__":
    r=main(sys.argv[1:])
    
def compile(filename, *options):
    return main(list(options)+[filename])
