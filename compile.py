import os,sys,getopt,hashlib,shutil,subprocess
import pycompile,ascompile
from run import getDirName,android_platform


#jar_name = 'papaya-gameengine-1.10.jar'
jar_name = 'jars'
def update_package(out_dir, config):
    replacements = {
        '$PACKAGE_NAME_PLACEHOLDER$': config.get('package_name', 'com.papaya.gamesdk.demo'),
        '$VERSION_CODE_PLACEHOLDER$': config.get('version_code', '1'),
        '$VERSION_NAME_PLACEHOLDER$': config.get('version_name', '1.0'),
        '$APP_NAME_PLACEHOLDER$': config.get('app_name', 'com.papaya.gamesdk.demo'),
        '$APP_ENABLE_1_PLACEHOLDER$': '<!--' if config.get('app_disable', 0) else '',
        '$APP_ENABLE_2_PLACEHOLDER$': '-->' if config.get('app_disable', 0) else '',
        '$WALLPAPER_NAME_PLACEHOLDER$': config.get('wallpaper_name', 'Wallpaper Demo'),
        '$WALLPAPER_DESCRIPTION_PLACEHOLDER$': config.get('wallpaper_desc', 'Just Cool!'),
        '$WALLPAPER_ENABLE_1_PLACEHOLDER$': '' if config.get('wallpaper_enable', 0) else '<!--',
        '$WALLPAPER_ENABLE_2_PLACEHOLDER$': '' if config.get('wallpaper_enable', 0) else '-->',
        '$WALLPAPER_SETTINGS_ENABLE$': 'android:settingsActivity="com.papaya.gamesdk.wallpaper.PPYWallpaperSettingsActivity"' if config.get('wallpaper_settings_url', 0) else '',
        '$INSTALL_LOCATION_PLACEHOLDER$': 'preferExternal' if config.get('install_location', 0) else 'auto',
    }

    s = open(os.path.join(out_dir, 'AndroidManifest.xml')).read()
    for i,j in replacements.items():
        s = s.replace(i,j)
    open(os.path.join(out_dir, 'AndroidManifest.xml'), 'w').write(s)
    s = open(os.path.join(out_dir, 'res', 'values', 'strings.xml')).read()
    for i,j in replacements.items():
        s = s.replace(i,j)
    open(os.path.join(out_dir, 'res', 'values', 'strings.xml'), 'w').write(s)
    s = open(os.path.join(out_dir, 'res', 'xml', 'papayawallpaper.xml')).read()
    for i,j in replacements.items():
        s = s.replace(i,j)
    open(os.path.join(out_dir, 'res', 'xml', 'papayawallpaper.xml'), 'w').write(s)
    if config.get('region','').upper()!='CHINA':
        os.remove(os.path.join(out_dir, 'assets', 'mobile_sp.apk'))
        os.remove(os.path.join(out_dir, 'jars', 'appflood-cn-1.3.jar'))
    else:
        os.remove(os.path.join(out_dir, 'jars', 'appflood-1.3.jar'))

def assert_config_keys(c, keys):
    valid = True
    for i in keys:
        if not c.get(i, None):
            print 'Invalid game.config, %s is empty'%i
            valid = False
    return valid

def mk_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

def execute(s):
    p = subprocess.Popen(s, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    r = p.communicate()[0]
    if p.returncode: return r

def generate_apk(out_dir, config, sdkdir, release = False, password=None, srcroot=None):
    print 'Exporting APK...'
    out_dir = os.path.abspath(out_dir)
    #os.chdir(out_dir)
    mk_dirs(os.path.join(out_dir,'bin','classes'))
    mk_dirs(os.path.join(out_dir,'gen'))
    if sdkdir:
        index = sdkdir.rfind(os.sep)
        sdk= os.path.split(os.path.split(sdkdir)[0])[0]
        platform = sdkdir
        #print sdk, platform
    else:
        sdk = os.path.abspath(getDirName())
        platform=os.path.join(sdk,'platforms',android_platform)
    toolsdir = os.path.join(sdk,'platform-tools')
    if not os.path.exists(toolsdir):
        toolsdir = os.path.join(platform,'tools')
    android_jar=os.path.join(platform,'android.jar')
    package_name=config.get('package_name')
    gen_file=os.path.join(out_dir,'gen',os.path.join(*package_name.split('.')),'R.java')
    debug_apk = os.path.join(out_dir,'bin','debug.apk')
    unaligned_apk = os.path.join(out_dir,'bin','unaligned.apk')

    err = execute('%s package -f -m -J %s -M %s -S %s -A %s -I %s  -F %s'%(
              os.path.join(toolsdir,'aapt'),
              os.path.join(out_dir,'gen'),
              os.path.join(out_dir,'AndroidManifest.xml'),
              os.path.join(out_dir,'res'),
              os.path.join(out_dir,'assets'),
              android_jar,
              os.path.join(out_dir,'bin','resource.ap_'),
              ))
    if err: print 'Exporting Error...',err
    err = execute('javac -d %s -sourcepath %s -bootclasspath %s -g %s'%(
              os.path.join(out_dir,'bin','classes'),
              os.path.join(out_dir,'gen'),
              android_jar,
              gen_file))
    if err: print 'Exporting Error...',err
    err = execute('%s --dex --output=%s %s %s'%(
              os.path.join(toolsdir,'dx'),
              os.path.join(out_dir,'bin','classes.dex'),
              os.path.join(out_dir,'bin','classes'),
              os.path.join(out_dir,jar_name)))
    if err: print 'Exporting Error...',err
    err = execute('%s %s -z %s -f %s -rf %s -rj %s'%(
              os.path.join(sdk,'tools','apkbuilder'),
              debug_apk,
              os.path.join(out_dir,'bin','resource.ap_'),
              os.path.join(out_dir,'bin','classes.dex'),
              os.path.join(out_dir,'libs'),
              os.path.join(out_dir,jar_name),
              ))
    if err:
        print 'Exporting Error...',err
        return False
    err = execute('%s %s -u -z %s -f %s -rf %s -rj %s'%(
          os.path.join(sdk,'tools','apkbuilder'),
          unaligned_apk,
          os.path.join(out_dir,'bin','resource.ap_'),
          os.path.join(out_dir,'bin','classes.dex'),
          os.path.join(out_dir,'libs'),
          os.path.join(out_dir,jar_name),
          ))
    if err:
        print 'Exporting Error...',err
        return False

    if release:
        alias_name = 'papaya_gameengine_developers'
        if srcroot:
            release_key = os.path.join(srcroot,'release-key.keystore')
        else:
            release_key = os.path.join('release-key.keystore')
        if not os.path.exists(release_key):
            err = os.system('keytool -genkey -v -keystore %s -alias %s -keyalg RSA -keysize 2048 -validity 10000'%(release_key, alias_name))
            if err:
                print 'Exporting Error...',err
                return False
        if not os.path.exists(release_key):
            print "Can't find release-key.keystore"
            return False
        release_apk = os.path.join(out_dir, 'bin', 'unaligned.apk')
        release_aligned_apk = os.path.join(out_dir, 'bin', 'release.apk')
        if password:
            err = os.system('jarsigner -keystore %s -keypass %s -storepass %s %s %s'%(release_key,password,password,release_apk,alias_name))
        else:
            err = os.system('jarsigner -keystore %s %s %s'%(release_key, release_apk, alias_name))
        if err:
            print 'Exporting Error...',err
            return False
        err = execute('jarsigner -verify %s'%release_apk)
        if err:
            print 'Exporting Error...',err
            return False
        err = execute('%s -v 4 %s %s'%(
            os.path.join(sdk,'tools','zipalign'),
            release_apk,
            release_aligned_apk
            ))
        if err:
            print 'Exporting Error...',err
            return False
    return True

def main(argv):
    try:
        optlist,args = getopt.getopt(argv, '', ['android=','src=','PC=','debug=','onlyscript=','pass=','skipcompile','ios'])
    except getopt.GetoptError,err:
        print "Can't find parameter"
        return
    dontpackage = False
    skipcompile = False
    ios = False
    params = []
    androidsdk = ''
    srcroot = None
    sdkdir = None
    onlyscript = 0
    password = None
    for o,aa in optlist:
        if o=='--PC':
            params += ['--PC',aa]
            dontpackage = True
        if o=='--skipcompile':
            skipcompile = True
        if o=='--ios':
            ios = True
        if o=='--android':
            sdkdir = aa
        if o=='--src':
            srcroot = aa
            args = [os.path.split(srcroot)[1]]+args
        if o=='--debug':
            params += ['--debug',aa]
        if o=='--onlyscript':
            dontpackage = (aa=="1")
        if o=='--pass':
            password = aa
    if not args:
        print "Please specify the project name."
        return
    project = args[0]
    release = True if len(args) > 1 and args[1] == 'release' else False
    if srcroot:
        project_dir = os.path.join(srcroot)
    else:
        project_dir = os.path.join('projects',project)
    resource_dir = os.path.join(project_dir,'res')
    config_file = os.path.join(project_dir,'game.config')
    if srcroot:
        if ios: out_dir = os.path.join(srcroot,'out',project+'.bundle')
        else: out_dir = os.path.join(srcroot,'out',project)
    else:
        if ios: out_dir = os.path.join('out',project+'.bundle')
        else: out_dir = os.path.join('out',project)
    fonts_input_dir = os.path.join(project_dir,'fonts')
    fonts_output_dir = os.path.join('assets','fonts')
    jars_input_dir = os.path.join(project_dir,'jars')
    jars_output_dir = 'jars'
    icon_input_dir = os.path.join(project_dir,'icons')
    icon_output_dir = os.path.join('res','drawable')
    image_input_dir = os.path.join(project_dir,'images')
    #image_output_dir = os.path.join('assets','web-resources','images')
    html_input_dir = os.path.join(project_dir,'pages')
    html_output_dir = os.path.join('assets','web-resources')
    if not os.path.exists(config_file):
        print "Can't find project. Please use 'create %s' to create a new project first."%project
        return
    config_content = open(config_file,'rb').read()
    config = dict(i.strip().split('=',1) for i in config_content.split('\n') if not i.startswith('#') and i.find('=')!=-1)

    if not assert_config_keys(config, ['script_name', 'social_key', 'base_url', 'orientation', 'package_name', 'app_name']):
        print 'Please check game.config'
        return

    script_name = config.get('script_name',None)
    script_out = script_name.split('.')[0] if script_name.find('.')!=-1 else script_name
    if ios: assets_dir = os.path.join(out_dir,'res')
    else: assets_dir = os.path.join(out_dir,'assets')
    game_dir = os.path.join(assets_dir,'game-resources')
    if os.path.exists(out_dir):
        for root, dirs, files in os.walk(out_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    mk_dirs(out_dir)
    if release:
        config_content+='\nbundle_script=0'

    assets = []
    def copyassets(src,dst):
        for i in os.listdir(os.path.join(src)):
            if i and not i.startswith('.'):
                s = os.path.join(src,i)
                d = os.path.join(assets_dir,dst,i)
                if os.path.isdir(s):
                    os.mkdir(d)
                    copyassets(os.path.join(src,i),os.path.join(dst,i))
                else:
                    shutil.copyfile(s,d)
                    assets.append(os.path.join(dst,i))

    if skipcompile:
        pass
    elif script_name.lower().endswith('.py') or script_name.lower().endswith('.pys'):
        ret = pycompile.compile(os.path.join(project_dir,script_name),'--out',os.path.join(project_dir,script_out),*params)
        if not ret:
            print 'Compile error'
            return
    elif script_name.lower().endswith('.as'):
        ret = ascompile.compile(params+['-o',os.path.join(project_dir,script_out),os.path.join(project_dir,script_name)])
        if not ret:
            print 'Compile error'
            return
    else:
        print 'Unknown file format'
        return
    if dontpackage:
        return

    if ios:
        # independent ios compile
        open(os.path.join(out_dir,'game.config'),'wb').write(config_content)
        s = open(os.path.join(project_dir,script_out),'rb').read()
        open(os.path.join(out_dir,script_out),'wb').write(s)
        mk_dirs(assets_dir)
        copyassets(resource_dir,'')
        print 'Please add directory %s to XCode.'%out_dir
        return
    template_dir = os.path.join('data','template')
    def copytemplates(src_dir,src,dst):
        for i in os.listdir(os.path.join(src_dir,src)):
            if i and not i.startswith('.'):
                s = os.path.join(src_dir,src,i)
                d = os.path.join(out_dir,dst,i)
                if os.path.isdir(s):
                    os.mkdir(d)
                    copytemplates(src_dir,os.path.join(src,i),os.path.join(dst,i))
                else:
                    shutil.copyfile(s,d)
    #shutil.copytree(os.path.join('data','template'), out_dir)
    copytemplates(template_dir,'','')
    if os.path.exists(fonts_input_dir):
        mk_dirs(os.path.join(out_dir,fonts_output_dir))
        copytemplates(fonts_input_dir,'',fonts_output_dir)
    if os.path.exists(jars_input_dir):
        copytemplates(jars_input_dir,'',jars_output_dir)
    if os.path.exists(icon_input_dir):
        copytemplates(icon_input_dir,'',icon_output_dir)
    #if os.path.exists(image_input_dir):
    #    copytemplates(image_input_dir,'',image_output_dir)
    if os.path.exists(html_input_dir):
        copytemplates(html_input_dir,'',html_output_dir)
    open(os.path.join(assets_dir,'game.config'),'wb').write(config_content)
    #shutil.copyfile(config_file, os.path.join(assets_dir,'game.config'))
    update_package(out_dir, config)

    mk_dirs(game_dir)
    s = open(os.path.join(project_dir,script_out),'rb').read()
    open(os.path.join(project_dir,script_out)+'.md5','wb').write(hashlib.md5(s).hexdigest())
    open(os.path.join(assets_dir,script_out),'wb').write(s)

    if os.path.exists(resource_dir):
        assets = []
        copyassets(resource_dir,'game-resources')
    open(os.path.join(assets_dir,'game-resources.lst'),'wb').write('\n'.join(i.replace('\\','/') for i in assets))

    assets = []
    if os.path.exists(image_input_dir):
        copyassets(image_input_dir,os.path.join('web-resources','images'))
    open(os.path.join(assets_dir,'web-resources.lst'),'ab').write('\n'.join(i.replace('\\','/') for i in assets))
    if generate_apk(out_dir, config, sdkdir, release, password, srcroot):
        shutil.copy(os.path.join(out_dir, 'bin', 'debug.apk'), os.path.join(project_dir, '%s-debug.apk'%project))
        if release:
            shutil.copy(os.path.join(out_dir, 'bin', 'release.apk'), os.path.join(project_dir, '%s-release.apk'%project))
    #copy game_background_landscape.jpg, game_background_portrait.jpg...


    # to be added



if __name__=="__main__":
    main(sys.argv[1:])
