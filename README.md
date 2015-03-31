Rookie Kit 2014
---------------

This is a two player battle game.  You
can customize the client anyway you want.

The client should run on any Python 2.7
with PyGame.

The server will only run on unix based
Python 2.7.  It has been tested on linux, 
but should work on OS X.

The server limitations on Windows are two-fold:

1- It is using poll() instead of select().  This 
   is straightforward to change.

2- It uses some multiprocessing.Process, which
   passes objects between processes.  That failed
   on Windows, and I didn't explore it.

To launch the server, run `main.py` in `server`.
By default this creates logging output.  So it
may be better to run `./main.py >& logfile.txt`.

To build your own client, it is probably best to
unpack `rookie-kit-2014.zip` and work from there.
The directories in the repository were meant to
set up the framework for a client.

