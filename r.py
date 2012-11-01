import sys,compile,run,inst,create,http_server
x = sys.argv[1]
locals()[x].main(sys.argv[2:])
