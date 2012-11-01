import os,getopt
import time, re, sys
import subprocess,urllib2,zipfile,tempfile
import progressbar
import colorama

curpath = os.path.abspath('.')
android_platform = 'android-16'
sdkdir = None
eclipse = None
#print curpath
#curpath = os.path.join(curpath,"tools")
LOG_TAG="papaya"
apk = ''
package= ''
activity = ''
name = ''
undertool = 1

helpstr= """
project-name ["release"] [emulator-name]
    run a project
    project-name indicates which porject you want to run
    "release" indicates that release version of the project will be ran. If this not specified debug version will be ran.
    emulator-name means the name of emulator on which you want to run the project.

-avds
    list all available emulators

-devices
    list all connected devices

-targets
    list all availble Android SDK's

-delete emulator-name
    delete an emulator

-create emulator-name [skin [target [path [size]]]]
    create an emulator
    The skin to use for this emulator, identified by name or dimensions. It is either <name> or <width>-<height>
    Target ID of the system image to use with the new emulator.
    Path to the location at which to create the directory for this emulator's files.
    the size of a new SD card image to create for this emulator.

-log ["e"]
    To view and follow the contents of the log buffers of the device
    "e" indicates whether print the log messages with error priority

-help
    Show help
"""

downlinks=[
        ['android-sdk-windows',
         'http://dl.google.com/android/android-sdk_r20.0.3-windows.zip',
         'http://dl.google.com/android/repository/android-16_r02.zip',
         'android-4.1.1',
         'http://dl.google.com/android/repository/platform-tools_r14-windows.zip',
        ],
	    ['android-sdk-macosx',
         'http://dl.google.com/android/android-sdk_r20.0.3-macosx.zip',
         'http://dl.google.com/android/repository/android-16_r02.zip',
         'android-4.1.1',
         'http://dl.google.com/android/repository/platform-tools_r14-macosx.zip',
        ],
	    ['android-sdk-linux',
         'http://dl.google.com/android/android-sdk_r20.0.3-linux.tgz',
         'http://dl.google.com/android/repository/android-16_r02.zip',
         'android-4.1.1',
         'http://dl.google.com/android/repository/platform-tools_r14-linux.zip',
        ]
]


def getDirName():
    if sdkdir:
        return ''
    else:
        return downlinks[getOSIndex()][0]

def getOSIndex():
    osindex = 2
    if sys.platform in ['darwin','mac']:
        osindex = 1
    elif sys.platform in ['win32','cygwin']:
        osindex = 0
    return osindex

def runcmd(c):
    if not undertool and c.startswith('adb'):
        path = os.path.join(curpath,getDirName(),'platform-tools',c)
    else:
        path = os.path.join(curpath,getDirName(),'tools',c)
    p = subprocess.Popen(path, shell=True, stdout=subprocess.PIPE, stdin = subprocess.PIPE,stderr=subprocess.STDOUT)
    return p


def getRunning():
    running = []
    p = runcmd('adb devices')
    s = p.communicate()[0]
    if s:
        ss = s.split('\n')
        #print ss[1:]
        add = 0
        for i in ss:
            if add and i.find('device')!=-1:
                running.append(i.split('\t')[0])
            if not add and i.find('List of devices attached')!=-1:
                add = 1
    print 'Running devices:', running
    return running



def createAVD(n,p=[]):
    s = '-s %s'%p[0] if p else ''
    t = '-t %s'%p[1] if len(p)>1 else '-t 1'
    path = '-p %s'%p[2] if len(p)>2 else ''
    c = '-c %s'%p[3] if len(p)>3 else ''
    p = runcmd('android create avd -n %s %s -f %s %s %s'%(n,t,c,path,s))
    s = p.communicate('n')[0]

    #return s.find("Created AVD '%s' based on"%n)!=-1
    return p.returncode == 0


def getAVD():
    p = runcmd('android list avds')
    s = p.communicate()[0]
    #print s
    avds = re.findall('Name: (.*)\n[^-]*API level 8',s)
    print 'Available avds:',avds
    return avds

def unlock():
    p1 = runcmd('adb -s %s shell sendevent /dev/input/event0 1 229 1'%name)
    p1.communicate()
    p1 = runcmd('adb -s %s shell sendevent /dev/input/event0 1 229 0'%name)
    p1.communicate()

def startActivity():
    global eclipse
    p1 = runcmd('adb -s %s shell pm list packages'%name)
    s = p1.communicate()[0]
    #print package,s.find(package)

    if s.find(package)==-1:
        p1 = runcmd('adb -s %s install %s'%(name,apk))
        s = p1.communicate()[0]
    else:
        p1 = runcmd('adb -s %s install -r %s'%(name,apk))
        s = p1.communicate()[0]
    if s.find('Failure')!=-1:
        print 'Try uninstalling...'
        p1 = runcmd('adb -s %s uninstall %s'%(name,package))
        s = p1.communicate()[0]
        p1 = runcmd('adb -s %s install -r %s'%(name,apk))
        s = p1.communicate()[0]
    if p1.returncode != 0:
        print p1.returncode,s
        return

    print 'Install %s successfully.'%apk
    if activity:
        print "Starting your application..."
        p1 = runcmd('adb -s %s shell am start -n %s/%s'%(name,package,activity))
        s = p1.communicate()
        if not eclipse:
            if getOSIndex() == 0:
                print 'Your application is running. Log info:'
                logcat(name)
            else:
                print 'To view logs, please input "./run.sh -log".'

def isFullyBoot():
    selected = '-s %s'%name if name else ""
    p1 = runcmd('adb %s wait-for-device shell ps'%selected)
    #p1 = runcmd('adb -s %s shell ps'%name)
    #time.sleep(1)
    #p1.poll()
    #if p1.returncode != None:
    ss = p1.communicate()[0]
    #print ' ps list:',ss
    #if ss: print 'find core process',ss.find('android.process.acore'),'phone: ',ss.find('com.android.phone')
    if ss and (ss.find("com.android.phone")!=-1 or ss.find("android.process.acore")!=-1):
        return True
    return False

def parseapk(path):
    global package,activity
    aaptPath = os.path.join(curpath,getDirName(),'platform-tools')
    if not os.path.exists(aaptPath):
        aaptPath = os.path.join(curpath,getDirName(),'platforms',android_platform,"tools")
    aapt = os.path.join(aaptPath,'aapt d badging %s'%path)
    p = subprocess.Popen(aapt, shell=True, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    #p = runcmd()
    s = p.communicate()[0]
    #print 'manifest:',s
    #v = re.search("package: name='([^\']+)' [\s\S]*launchable activity name='([^\']+)'",s)
    #package,activity = v.group(1),v.group(2)
    v = re.search("package: name='([^\']+)'",s)
    package = v.group(1)
    v = re.search("[\s\S]*launchable[ -]activity[:]? name='([^\']+)'",s)
    if v:
        activity = v.group(1)
    #print package,activity


def deleteAVD(n):
    #print n
    if n and type(n[0])==str:
        p = runcmd('android delete avd -n %s'%n[0])
        s = p.communicate()[0]
        #print s
        if s.find('Error')!=-1:
            print '%s has been deleted'%n[0]
    else:
        print "Invalidated emulator's name."

def targets():
    p1 = runcmd('android list targets')
    print p1.communicate()[0]

def logcat(avd=None, pe = None):
    if not avd:
        running = getRunning()
        if running:
            if len(running)>1:
                for i in range(len(running)):
                    print 'id %d:'%i,running[i]
                print 'More available devices. Please input the index of the device whose log buffers you want to view:',
                pp= raw_input()
                while not (pp and pp.isdigit() and int(pp)<len(running)):
                    for i in range(len(running)):
                        print 'id %d:'%i,running[i]
                    print 'Wrong index, please input again:',
                    pp= raw_input()
                avd = running[int(pp)]
            else:
                avd = running[0]
        else:
            print 'No AVD is running.'
            return
    colorama.init()
    avd = "-s %s"%avd if avd else ''
    p = runcmd('adb %s logcat -c'%avd)
    p.communicate()
    try:
        #logpipe = runcmd('adb %s logcat -v tag %s:V DEBUG:I %s'%(avd,LOG_TAG, '*:E' if pe else '*:S'))
        logpipe = runcmd('adb %s logcat -v time %s:V DEBUG:I %s'%(avd,LOG_TAG, '*:E' if pe else '*:S'))
        while 1:
            s = logpipe.stdout.readline()
            printlog(s)
            if not s: time.sleep(0.5)
    except KeyboardInterrupt, e:
        print 'exit logcat'





def printlog(s):
    if s == None: return

    for i in s.split("\n"):
        c = ""
        start = i[19:]
        if start.startswith("D"):
            c = colorama.Fore.CYAN
        elif start.startswith("I"):
            c = colorama.Fore.GREEN
        elif start.startswith("W"):
            c = colorama.Fore.YELLOW
        elif start.startswith("E"):
            c = colorama.Fore.RED
        elif start.startswith("F"):
            c = colorama.Fore.MAGENTA
            #c = colorama.Fore.CYAN
        if i:
            print c+i+colorama.Fore.RESET


def runcmd2(*args):
    if not undertool and args[0].startswith('adb'):
        path = os.path.join(curpath,getDirName(),'platform-tools',args[0])
    else:
        path = os.path.join(curpath,getDirName(),'tools',args[0])
    args= [path]+list(args[1:])
    if getOSIndex() == 0:
        p = os.spawnv(os.P_DETACH,path,args)
    else:
        p = os.spawnv(os.P_NOWAIT,path,args)
    return p
    #p = subprocess.Popen(path, shell=True, stdout=subprocess.PIPE, stdin = subprocess.PIPE,stderr=subprocess.STDOUT)
    #return p


def run(a,p=None):
    global name,apk

    avd = p[0] if p else None
    #ret = createAVD(n)
    apk = a
    parseapk(apk)
    succ = 1
    if name=='':
        running = getRunning()
        succ = 0
        if running:
            if len(running)>1:
                for i in range(len(running)):
                    print 'id %d:'%i,running[i]
                print 'More available devices. Please input the index of the device that you want to run:',
                pp= raw_input()
                while not (pp and pp.isdigit() and int(pp)<len(running)):
                    for i in range(len(running)):
                        print 'id %d:'%i,running[i]
                    print 'Wrong index, please input again:',
                    pp= raw_input()
                name = running[int(pp)]
            else:
                name = running[0]
            succ = 1
        else:
            avds = getAVD()
            if not avds:
                if createAVD('ppy_emulator'):
                    avd = 'ppy_emulator'
                    name = 'emulator-5554'
                    succ = 1
            if (avd and avd in avds):
                pass
            elif len(avds)==1:
                avd = avds[0]
            elif not avd or avd not in avds:
                for i in range(len(avds)):
                    print 'id %d:'%i, avds[i]
                print 'Please input the index of emulators that you want to run:',
                pp = raw_input()
                while not (pp and pp.isdigit() and int(pp)< len(avds)):
                    for i in range(len(avds)):
                        print 'id %d:'%i, avds[i]
                    print 'Wrong index, please input again:',
                    pp = raw_input()
                avd = avds[int(pp)]
            print 'Selected avd:',avd

            p = runcmd2('emulator', '-avd',avd, '-no-boot-anim', '-port','5554')
            time.sleep(1)
            #p.poll()
            #print rr,p.returncode
            #if p.returncode == None:
            if p>=0:
                name = "emulator-%d"%(5554)
                succ = 1
            else:
                print "Failed to start emulator"

    if not succ:
        print 'No Device'
    else:
        print 'Device name:',name
        print 'Waiting for the device'
        while True:
            if isFullyBoot():
                print '%s has fully booted.'%name
                unlock()
                startActivity()
                break
            else:
                time.sleep(5)
    print 'end'

    #for i in z.namelist():
    #    if i== 'android-2.2_r02-windows/templates/':
    #        z.extractall('templates',i)

def checkadbpos():
    global undertool
    path = os.path.join(curpath,getDirName(),'platform-tools')
    if os.path.exists(path):
        undertool = 0

def main(argv):
    global sdkdir,curpath,android_platform,name,eclipse
    if not argv:
        print helpstr
        return
    checkadbpos()
    cmd = argv[0]
    p = argv[1:]
    if cmd == '-install' and p:
        run(p[0],p[1:])
    elif cmd == '-devices':
        getRunning()
    elif cmd == '-avds':
        getAVD()
    elif cmd == '-create':
        if createAVD(p[0],p[1:]):
            print '"%s" has been created.'%p[1]
    elif cmd == '-delete':
        deleteAVD(p)
    elif cmd == '-targets':
        targets()
    elif cmd == '-help':
        print helpstr
    elif cmd == '-log':
        logcat(None ,1 if p else None)
    else:
        try:
            optlist,args = getopt.getopt(argv, '', ['android=','src=','device='])
        except getopt.GetoptError,err:
            print "Can't find parameter"
            return
        srcroot = None
        for o,aa in optlist:
            if o=='--android':
                sdkdir = aa
            if o=='--src':
                data = os.path.split(aa)
                srcroot = aa
                args = [data[1]]+args
                eclipse = 1
            if o=='--device':
                name = aa
        if sdkdir:
            data = os.path.split(sdkdir)
            android_platform = data[1]
            curpath = os.path.split(data[0])[0]
            checkadbpos() #check again
        app = args[0]
        p = args[1:]
        if not srcroot:
            srcroot = os.path.join(os.path.abspath('.'),'projects',app)
        if p and p[0]=='release':
            a = os.path.join(srcroot,'%s-release.apk'%app)
            p = p[1:]
        else:
            a = os.path.join(srcroot,'%s-debug.apk'%app)
        #a = os.path.join(curpath,a)
        if not os.path.exists(a):
            print 'Cannot find ',a
        else:
            try:
                run(a,p)
            except Exception,ex:
                print ex

if __name__=="__main__":
    main(sys.argv[1:])

