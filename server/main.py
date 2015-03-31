#!/usr/bin/env python
import logging, sys, getopt
sys.path.append('..')
from main_server import MainServer

def usage():
    print "usage: %s [-L|--logging level] [-h|--help]" % (sys.argv[0])
    print "-L|--logging info|debug|warning|error: logging level"
    print "-h|--help        : show this message and exit"
    return

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hL:", ["help", "logging="])
    except getopt.GetoptError as e:
        print str(e)
        usage()
        sys.exit(1)

    show_help = False
    logging_level = "info"
    for o, a in opts:
        if o in ("-h", "--help"):
            show_help = True
        elif o in ("-L", "--logging"):
            logging_level = a
        else:
            print "Unexpected option: %s" % (o)
            usage()
            sys.exit(1)
    if show_help:
        usage()
        sys.exit(1)

    FORMAT = '%(asctime)-15s %(levelname)s:%(name)s:%(filename)s:%(lineno)d:%(message)s'
    if logging_level == "info":
        logging.basicConfig(level=logging.INFO,format=FORMAT)
    elif logging_level == "debug":
        logging.basicConfig(level=logging.DEBUG,format=FORMAT)
    elif logging_level == "warning":
        logging.basicConfig(level=logging.WARNING,format=FORMAT)
    elif logging_level == "error":
        logging.basicConfig(level=logging.ERROR,format=FORMAT)
    else:
        logging.basicConfig(level=logging.ERROR,format=FORMAT)


    server = MainServer()
    server.run()
    return

if __name__ == "__main__":
    main()

