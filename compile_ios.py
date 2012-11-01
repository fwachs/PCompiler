import os,sys,getopt,hashlib,shutil,subprocess
import pycompile,ascompile
from run import getDirName

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

def main(argv):
    try:
        optlist,args = getopt.getopt(argv, '', ['PC=','skipcompile'])
    except getopt.GetoptError,err:
        print "Can't find parameter"
        return
    dontpackage = False
    skipcompile = False
    params = []
    for o,aa in optlist:
        if o=='--PC':
            params += ['--PC',aa]
            dontpackage = True
        if o=='--skipcompile':
            skipcompile = True
    #project = args[0]
    project = 'housewifewars'
    release = True if len(args) > 1 and args[1] == 'release' else False
    project_dir = os.path.join('projects',project)
    resource_dir = os.path.join(project_dir,'res')
    config_file = os.path.join(project_dir,'game.config')
    out_dir = os.path.join(project_dir,project+'.bundle')
    
    fonts_dir = os.path.join(project_dir,'fonts')
    image_dir = os.path.join(project_dir,'images')
    #image_output_dir = os.path.join('assets','web-resources','images')
    #html_input_dir = os.path.join(project_dir,'pages')
    #html_output_dir = os.path.join('assets','web-resources')
    if not os.path.exists(config_file):
        print "Can't find project. Please use 'create %s' to create a new project first."%project
        return
    config_content = open(config_file,'rb').read()
    config = dict(i.strip().split('=',1) for i in config_content.split('\n') if not i.startswith('#') and i.find('=')!=-1)

    if not assert_config_keys(config, ['script_name', 'social_key', 'base_url', 'orientation']):
        print 'Please check game.config'
        return

    script_name = config.get('script_name',None)
    script_out = script_name.split('.')[0] if script_name.find('.')!=-1 else script_name
    assets_dir = os.path.join(out_dir,'res')
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

    
    # independent ios compile
    open(os.path.join(out_dir,'game.config'),'wb').write(config_content)
    s = open(os.path.join(project_dir,script_out),'rb').read()
    open(os.path.join(project_dir,script_out)+'.md5','wb').write(hashlib.md5(s).hexdigest())
    open(os.path.join(out_dir,script_out),'wb').write(s)
    mk_dirs(assets_dir)
    copyassets(resource_dir,'')
    fonts_dir = os.path.join(project_dir,'fonts')
    image_dir = os.path.join(project_dir,'images')
    copyassets(fonts_dir,'')
    copyassets(image_dir,'')
    print 'Please add directory %s to XCode.'%out_dir
    
    '''
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
    if os.path.exists(icon_input_dir):
        copytemplates(icon_input_dir,'',icon_output_dir)
    #if os.path.exists(image_input_dir):
    #    copytemplates(image_input_dir,'',image_output_dir)
    if os.path.exists(html_input_dir):
        copytemplates(html_input_dir,'',html_output_dir)
    open(os.path.join(assets_dir,'game.config'),'wb').write(config_content)
    #shutil.copyfile(config_file, os.path.join(assets_dir,'game.config'))
    

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
    '''
    #copy game_background_landscape.jpg, game_background_portrait.jpg...

    
    # to be added


    
if __name__=="__main__":
    main(sys.argv[1:])
