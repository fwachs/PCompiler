import os, sys, re

curpath = os.path.abspath('.')

configtemp = """
script_name=%s
base_url=%s
social_key=%s
orientation=%s
package_name=%s
app_name=%s
social_game=%d
force_update=%d
"""

def mkdir(d):
    if not os.path.exists(d):
        os.mkdir(d)

def main(args):
    project = ''
    if args:
        project = args[0]
    if project:
        path = os.path.join(curpath,'projects',project)
        if os.path.exists(path):
            print 'The project called "%s" exists already.'%project
            return
        
        print "The URL of repository server (http://xx.xx.xx.xx/)."
        ip = raw_input()
        while not (ip and re.match("http[s]{0,1}://[\d\D]*\.[\d\D]*",ip)):
            if not ip:
                ip = 'http://127.0.0.1/'
                break
            print 'Wrong server URL format, try again:'
            ip = raw_input()
        
        
        print 'Language: 0-ActionScript, 1-Python'
        index = raw_input()
        while not (index.isdigit() and int(index)<2):
            print 'Language: 0-ActionScript, 1-Python'
            index = raw_input()
        script  = project+'.'+['as','pys'][int(index)]
        
        
        print 'Papaya Social Key: (http://papayamobile.com/developer/ )'
        skey = raw_input()
        if not skey:
            skey = '54SO2c8ZwFLINBtn'
            
        print 'Select the game orientation:'
        print 'id:0, LANDSCAPE'
        print 'id:1, PORTRAIT'
        print 'id:2, USER DEFINED'
        ori = raw_input()
        while not (ori.isdigit() and int(ori) < 3 ):
            print 'Select your game orientation:'
            print 'id:0, LANDSCAPE'
            print 'id:1, PORTRAIT'
            print 'id:2, USER DEFINED'
            ori = raw_input()
            
        print "Package name (com.xxx.yyy):"
        package = raw_input()
        while not (package and package.find('.')>0 and not package.endswith('.')):
            print "Package name (should contain at least one '.' separator):"
            package = raw_input()
            
            
        print 'App name:'
        name = raw_input()
        while not name:
            print 'App name:'
            name = raw_input()
        
        #print "Does the game support offline mode (y/n)?[y]"
        #social = raw_input()
        #social = 1 if social.lower() =="n" else 0
        social = 0
        
        #print "Have to download the latest script to play the game(y/n)?[n]"
        #up = raw_input()
        #up = 1 if up.lower() =="y" else 0
        force_up = 0
        
        mkdir(path)
        mkdir(os.path.join(path,'res'))    
        conf = configtemp%(script,ip,skey,ori,package,name,social,force_up)
        open(os.path.join(path,'game.config'),'wb').write(conf)
        open(os.path.join(path,script),'wb')
        print 'Create project "%s" successfully!'%project
        
    else:
        print 'Please specify the project name.'
    

#os.chdir(curpath)
#main()
if __name__=="__main__":
    main(sys.argv[1:])