import os
import re, sys
import subprocess,urllib2,zipfile,tarfile
import progressbar,run
from run import downlinks,android_platform


curpath = os.path.abspath('.')
#print curpath
#curpath = os.path.join(curpath,"tools")

def install():
    i = run.getOSIndex()
    if not os.path.exists(os.path.join(downlinks[i][0])):
        downloadSDK(downlinks[i][1])
        fname = downlinks[i][1].split('/')[-1]
        unzip(fname)
        if os.path.exists(fname): os.remove(fname)

    if not os.path.exists(os.path.join(downlinks[i][0],'platform-tools')):
        downloadSDK(downlinks[i][4],'Downloading Android SDK Platform-tools')
        fname = downlinks[i][4].split('/')[-1]
        unzip(fname,os.path.join(downlinks[i][0]))
        rname = os.path.join(downlinks[i][0],fname.split('.')[0])
        if os.path.exists(rname):
            os.rename(rname,os.path.join(downlinks[i][0],'platform-tools'))
        if os.path.exists(fname): os.remove(fname)


    if not os.path.exists(os.path.join(downlinks[i][0],'platforms',android_platform)):
        downloadSDK(downlinks[i][2])
        fname = downlinks[i][2].split('/')[-1]
        unzip(fname,os.path.join(downlinks[i][0],'platforms'))
        #rename
        rname = os.path.join(downlinks[i][0],'platforms',downlinks[i][3])
        if os.path.exists(rname):
            os.rename(rname,os.path.join(downlinks[i][0],'platforms',android_platform))

        if os.path.exists(fname): os.remove(fname)
    if i == 0:
        p = subprocess.Popen('set ANDROID_SDK_ROOT=%s'%os.path.join(downlinks[i][0]), shell=True, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        p.communicate()
    else:
        for j in ["adb","emulator","android","apkbuilder"]:
            cmdp = os.path.join(downlinks[i][0],'tools',j)
            if os.path.exists(cmdp):
                p = subprocess.Popen('chmod 755 %s'%cmdp, shell=True, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                p.communicate()
        for j in ["aapt","dx"]:
            p = subprocess.Popen('chmod 755 %s'%os.path.join(downlinks[i][0],'platform-tools',j), shell=True, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            p.communicate()

        cmdp = os.path.join(downlinks[i][0],'platform-tools',"adb")
        if os.path.exists(cmdp):
            p = subprocess.Popen('chmod 755 %s'%cmdp, shell=True, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            p.communicate()

    run.createAVD('ppy_emulator')
    print 'Congratulations! You have finished the installation of Papaya Game Engine.'


def downloadSDK(url,t = 'Downloading Android SDK',name=None,block_size=1024):
    if not name:
        name= url.split('/')[-1]
    data = urllib2.urlopen(url)
    allsize =  data.info().getheader('Content-Length')

    path = os.path.join(name)

    #print 'File size to be donwloaded:',allsize,path
    #print os.path.getsize(path)==long(allsize)
    #return
    if not os.path.exists(path) or os.path.getsize(path) != long(allsize):
        print 'Start downloading %s. If you downloaded before, please place it in this directory, and restart the installation.'%name
        #if os.path.exists(path): os.remove(path)
        f = open(name, 'wb')
        widgets = ['%s: '%t, progressbar.Percentage(), ' ', progressbar.Bar(marker=progressbar.RotatingMarker()),
                       ' ', progressbar.ETA(), ' ', progressbar.FileTransferSpeed()]
        pbar = progressbar.ProgressBar(widgets=widgets, maxval=float(allsize)).start()
        downloaded = 0
        d = data.read(block_size)
        size = len(d)
        downloaded += size
        f.write(d)
        while size >= block_size:
            d = data.read(block_size)
            size = len(d)
            downloaded += size
            pbar.update(downloaded)
            f.write(d)
        f.close()
    else:
        pass
        #print '%s has been downloaded'%name

def create(d):
    if not os.path.exists(d):
        os.mkdir(d)

def unzip(f,p='.'):
    print "Extracting files..."
    if f.endswith('.tgz'):
        tar = tarfile.open(f)
        tar.extractall(p)
        tar.close()
    else:
        z = zipfile.ZipFile(f)
        for i in z.namelist():
            path = os.path.join(p, i)
            if i.endswith('/'):
                create(path)
            else:
                create(os.path.dirname(path))
                file(path, 'wb').write(z.read(i))
        z.close()


def main(argv):
    print 'Welcome to Papaya Game Engine.'

    p = subprocess.Popen('java -version', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.communicate()
    s = p.returncode
    p1 = subprocess.Popen('javac -help', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p1.communicate()
    s1 = p1.returncode
    if s != 0 or s1!=0: #
        print 'JDK cannot be found. Please install it first and start the installation again.'
        return
    install()

if __name__=="__main__":
    main(sys.argv)
#downloadSDK('https://dl-ssl.google.com/android/repository/android-2.2_r02-macosx.zip')
#unzip('android-sdk_r07-linux_x86.tgz')

