#Copyright Jon Berg , turtlemeat.com

import string,cgi,time,sys,os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
#import pri
project = ''

class MyHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            #p = os.path.join(curdir,'projects',project,self.path)
            p = os.path.join('projects', project) #self.path has /test.html    
            for i in self.path.split('/'):
                p = os.path.join(p,i)
            #note that this potentially makes every file on your computer readable by the internet
            if os.path.exists(p):
                self.send_response(200)
                if self.path.lower().endswith(".png"):
                    #f = open(p)
                    self.send_header('Content-type',	'image/png')
                elif self.path.lower().endswith('.jpg') or self.path.endswith('.jpeg'):
                    self.send_header('Content-type',    'image/jpg')
                else:
                    self.send_header('Content-type',    'application/octet-stream')
                    
                self.end_headers()
                self.wfile.write(open(p,'rb').read())
                #f.close()
                return
            else:
                self.send_error(404,'File Not Found: %s' % self.path)
            return
                
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)
     

    def do_POST(self):
        global rootnode
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query=cgi.parse_multipart(self.rfile, pdict)
            self.send_response(301)
            
            self.end_headers()
            upfilecontent = query.get('upfile')
            print "filecontent", upfilecontent[0]
            self.wfile.write("<HTML>POST OK.<BR><BR>");
            self.wfile.write(upfilecontent[0]);
            
        except :
            pass

def main(p):
    global project
    try:
        project = p[0]
        server = HTTPServer(('', 80), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main(sys.argv[1:])

