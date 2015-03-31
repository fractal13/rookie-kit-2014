#!/usr/bin/env python
import sys, logging, getopt
sys.path.append('..')
from ai_client import AiClient
from config import *

def usage():
    print "usage: %s [-l|--localhost] [-s|--server host] [-L|--logging level] [-n|--name name] [-a|--ai] [-h|--help]" % (sys.argv[0])
    print "-l|--localhost   : use localhost for the server"
    print "-s|--server host : identify the host of the server"
    print "-L|--logging info|debug|warning|error: logging level"
    print "-n|--name name   : display name in game"
    print "-a|--ai          : play as AI"
    print "-h|--help        : show this message and exit"
    return

def main(argv):
    try:
        opts, args = getopt.getopt(argv[1:], "hs:lL:n:a", ["help", "server=", "localhost", "logging=", "name=", "ai"])
    except getopt.GetoptError as e:
        print str(e)
        usage()
        sys.exit(1)

    show_help = False
    server = "rookie.cs.dixie.edu"
    name = DEFAULT_TEAM_NAME
    logging_level = "error"
    do_ai = False
    for o, a in opts:
        if o in ("-h", "--help"):
            show_help = True
        elif o in ("-s", "--server"):
            server = a
        elif o in ("-l", "--localhost"):
            server = "127.0.0.1"
        elif o in ("-L", "--logging"):
            logging_level = a
        elif o in ("-n", "--name"):
            name = a
        elif o in ("-a", "--ai"):
            do_ai = True
        else:
            print "Unexpected option: %s" % (o)
            usage()
            sys.exit(1)
    if show_help:
        usage()
        sys.exit(1)

    if logging_level == "info":
        logging.basicConfig(level=logging.INFO)
    elif logging_level == "debug":
        logging.basicConfig(level=logging.DEBUG)
    elif logging_level == "warning":
        logging.basicConfig(level=logging.WARNING)
    elif logging_level == "error":
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.ERROR)
    
    g = AiClient(name, server)
    g.set_ai(do_ai)
    g.main_loop()
    return

if __name__ == "__main__":
    main(sys.argv)
