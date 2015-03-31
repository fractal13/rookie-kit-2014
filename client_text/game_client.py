import socket, select, sys, logging
from common.game_comm import *
from engine_client.game_engine import ClientGameEngine
from client.client_game_socket import ClientGameSocket

class GameCommandPrompt:
    """Support for stdin/stdout communication with the user."""
    
    def __init__(self, readpoll, game_socket):
        self.logger = logging.getLogger('GameCommandPrompt')
        self.readpoll = readpoll
        self.readpoll.register(sys.stdin, select.POLLIN)
        self.game_socket = game_socket
        return

    def prompt(self):
        sys.stdout.write("game) ")
        sys.stdout.flush()
        return

    def is_ready(self, fd):
        return sys.stdin and fd == sys.stdin.fileno()

    def process_event(self, engine):
        done = False
        original_line = sys.stdin.readline()
        line = original_line.strip()
        words = line.split(' ')
        if len(words) > 0:
            if words[0] == 'echo':
                gc = GameComm(self.game_socket.get_sock())
                msg = GameMessageEcho()
                msg.set_text(' '.join(words[1:]))
                if not gc.write_mesg(msg):
                    self.logger.error("Error in write_mesg.")
            elif words[0] == 'broadcast':
                gc = GameComm(self.game_socket.get_sock())
                msg = GameMessageBroadcast()
                msg.set_text(' '.join(words[1:]))
                if not gc.write_mesg(msg):
                    self.logger.error("Error in write_mesg.")
            elif words[0] == 'login':
                if len(words) > 1:
                    gc = GameComm(self.game_socket.get_sock())
                    msg = GameMessageLogin()
                    msg.set_user(words[1])
                    msg.set_request(True)
                    if not gc.write_mesg(msg):
                        self.logger.error("Error in write_mesg.")
                else:
                    print "Usage: login username"
            elif words[0] == 'stop':
                engine.set_player_speed_stop()
            elif words[0] == 'slow':
                engine.set_player_speed_slow()
            elif words[0] == 'medium':
                engine.set_player_speed_medium()
            elif words[0] == 'fast':
                engine.set_player_speed_fast()
            elif words[0] == 'degrees':
                if len(words) > 1:
                    try:
                        degrees = float(words[1])
                        engine.set_player_direction(degrees)
                    except:
                        print "Usage: degrees 0-360"
                else:
                    print "Usage: degrees 0-360"
            elif words[0] == 'quit' or words[0] == 'exit' or len(original_line) == 0:
                if len(original_line) == 0:
                    print
                if words[0] == "quit":
                    done = True
                self.game_socket.disconnect_from_server()
            else:
                print "Known commands: echo, broadcast, login, quit, exit, stop, slow, medium, fast, degrees"
        return done


class GameClient:
    """Runs the game client"""

    def __init__(self, server_host="127.0.0.1", server_port=20149):
        self.logger = logging.getLogger('GameClient')
        self.logger.debug('__init__')
        self.server_host = server_host
        self.server_port = server_port
        self.done = False
        return

    def restart(self):
        self.readpoll = select.poll()
        self.game_socket = ClientGameSocket(self.readpoll, self.server_host, self.server_port)
        self.game_socket.connect_to_server()
        self.command = GameCommandPrompt(self.readpoll, self.game_socket)
        self.done = False
        return
        

    def run_one(self):
        self.restart()
        self.engine = ClientGameEngine()
        while self.game_socket.get_sock():
            self.command.prompt()
            ready_list = self.readpoll.poll()
            
            # process inputs
            for (fd, event) in ready_list:
                if self.game_socket.is_ready(fd):
                    self.game_socket.process_event(self.engine)
                elif self.command.is_ready(fd):
                    self.done = self.command.process_event(self.engine)
                else:
                    self.logger.error("Unknown fd: ", fd)

            # send messages
            self.game_socket.send_messages(self.engine)
            # update display
            print self.engine

        return
        
    def run(self):
        while not self.done:
            self.run_one()
        return
    
def main():
    g = GameClient()
    g.run()
    return
                
                
                
if __name__ == "__main__":
    main()
    
