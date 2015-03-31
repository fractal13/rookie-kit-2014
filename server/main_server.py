from multiprocessing import Process
import socket, select, logging, errno, sys, random
import game_server
from common.game_comm import *
from common.game_message import *
from main_server_client import *
from tournament import Tournament
import client_ai.main

class MainServer:
    """
    Accepts pairs of connections and spawns game server to handle the game.

    Modifying to
    - accept client connections, keep them in a queue.
    - handle messages from clients,
      + login
        -> take name and keep paired with socket (database some day)
        <- send acknowledgement message
      + request game dual
        -> pair with next client that wants a dual
        <- send periodic wait message
      + request game single
        -> pair with a computer spawned player
        <- send acknowledgement message
      + request game tournament
        -> put in tournament pool
        <- send acknowledgement message
      + request to be AI
        -> pair with a user who wants to player single game
        <- send acknowledgement message
      + request to view
        -> put in viewer queue, allow to view next viewerless match
        <- send acknowledgement message

      + request active game list
        -> find list of active games (from database maybe?)
        <- send message with list of game ids?
      + request active game view
        -> receive connection, hand to translater process
           that communicates with the game.  requires
           game server to receive new connections, or
           have a display pipe communication built in
        <- send nothing?
      + closed socket
        -> close socket
    """

    def __init__(self, ip="0.0.0.0", port=20149, listen_count=8):
        self.logger = logging.getLogger('MainServer')
        self.logger.debug('__init__')
        self.ip = ip
        self.port = port
        self.listen_count = listen_count
        self.sock = None
        self.poll = None
        self.done = False
        self.clients = [] # list of MainServerClient objects waiting for action
        self.processes = []
        self.tournament = Tournament()
        self.tournament.open()
        return

    def prepare_socket(self):
        """Creates a socket, and prepares it to accept new connections."""
        self.logger.debug('prepare_socket')

        try:
            # build the listening socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # reuse socket if previous instance is in WAIT state
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # bind to address
            self.sock.bind( (self.ip, self.port) )
            # set maximum listen queue size
            self.sock.listen(self.listen_count)
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                self.logger.info("%s:%d %s", self.ip, self.port, e.strerror)
            else:
                self.logger.error("socket.error: %s", e)
            raise

        return

    def close_socket(self):
        if self.sock:
            self.sock.close()
            self.sock = None
        return
        
    def prepare_poll(self):
        """Creates a poll, and prepares it to watch the accept socket."""
        self.logger.debug('prepare_poll')
        
        self.poll = select.poll()
        if self.sock:
            self.poll.register(self.sock.fileno(), select.POLLIN)
        return

    def get_next_viewer(self):
        v0 = None
        i = 0
        while i < len(self.clients):
            if self.clients[i].state == MS_STATE_VIEWER:
                v0 = self.clients.pop(i)
                self.remove_client(v0.sock)
                break
            i += 1
        return v0
        
    def spawn_game(self, dualers):
        dualers.sort()
        # pop higher index first
        c1 = self.clients.pop(dualers[1])
        c0 = self.clients.pop(dualers[0])
        self.remove_client(c0.sock)
        self.remove_client(c1.sock)
        #
        c0.opponent_name = c1.name
        msg = GameStartingMessage(c0.opponent_name)
        self.send_client_socket_message(c0.sock, msg)
        #
        c1.opponent_name = c0.name
        msg = GameStartingMessage(c1.opponent_name)
        self.send_client_socket_message(c1.sock, msg)
        #
        v0 = self.get_next_viewer()
        if v0:
            v0.name = c0.name
            v0.opponent_name = c0.opponent_name
            msg = GameStartingMessage(v0.opponent_name)
            self.send_client_socket_message(v0.sock, msg)
        
        self.logger.info('spawning game for %s vs %s.', c0.address, c1.address)
        p = Process(target=game_server.main, args=(c0, c1, v0,))
        p.start()
        self.processes.append(p)

    def spawn_ai(self):
        self.logger.info('spawning ai.')
        name = random.choice([ "Alexander", "Ajax", "Bellatrix", "Mars", "Shogun", ])
        p = Process(target=client_ai.main.main, args=(["", "--localhost", "--name", name, "--ai", ],))
        p.start()
        self.processes.append(p)
        return
        
    def spawn_dual_game(self):
        """If there are at least 2 dual connections, spawn a game."""
        self.logger.debug('spawn_game')
        dualers = []

        i = 0
        while i < len(self.clients) and len(dualers) < 2:
            if self.clients[i].state == MS_STATE_WAIT_DUAL_GAME:
                dualers.append(i)
            i += 1
        
        if len(dualers) >= 2:
            self.spawn_game(dualers[:2])
        return

    def spawn_single_game(self):
        """
        Try to find one MS_STATE_WAIT_SINGLE_GAME and one MS_STATE_AI_PLAYER.
        Pair them together for a game.

        If there are no MS_STATE_AI_PLAYERs, spawn an AI.
        """
        self.logger.debug('spawn_single_game')
        singles = []
        ais = []

        i = 0
        while i < len(self.clients) and (len(singles) < 1 or len(ais) < 1):
            if self.clients[i].state == MS_STATE_WAIT_SINGLE_GAME:
                singles.append(i)
            elif self.clients[i].state == MS_STATE_AI_PLAYER:
                ais.append(i)
            i += 1

        if len(singles) >= 1 and len(ais) >= 1:
            dualers = [ singles[0], ais[0] ]
            self.spawn_game(dualers[:2])
        elif len(singles) >= 1 and len(ais) < 1:
            self.spawn_ai()
        else:
            self.logger.error("spawn_single_game should not have been called.")
        return

    def spawn_tournament_game(self):
        """If there are at least 2 tournament connections, spawn a game."""
        self.logger.debug('spawn_tournament_game')
        eligible = []
        eligible_players = self.tournament.get_eligible_players()

        i = 0
        while i < len(self.clients):
            if (self.clients[i].state == MS_STATE_WAIT_TOURNAMENT_GAME and
                self.clients[i].name in eligible_players):
                eligible.append(i)
            i += 1

        # have full list of eligible, connected players
        dualers = []
        if len(eligible) >= 2:
            # try to find a match of 2 players who haven't played
            for i in range(len(eligible)):
                n1 = self.clients[eligible[i]].name
                for j in range(i+1, len(eligible)):
                    n2 = self.clients[eligible[j]].name
                    if not self.tournament.either_game_exists(n1, n2):
                        dualers = [eligible[i],eligible[j]]
                        break
                if len(dualers) >= 2:
                    break

        if len(dualers) >= 2:
            self.tournament.add_game(self.clients[dualers[0]].name, self.clients[dualers[1]].name)
            self.spawn_game(dualers[:2])
        else:
            self.logger.warn("No tournament game spawned. dualers: %d eligible: %d  eligible_players: %d",
                             len(dualers), len(eligible), len(eligible_players))
        return


    def join_processes(self):
        """Checks if any of the child processes have finished."""
        self.logger.debug('join_processes')

        for i in range(len(self.processes)):
            self.processes[i].join(0.000001)
            if not self.processes[i].is_alive():
                self.logger.debug('Removing process %s.', self.processes[i])
                self.processes[i] = None
                
        processes = []
        for p in self.processes:
            if p:
                processes.append(p)
        self.processes = processes
        return

    def accept_new_client(self):
        (connection, address) = self.sock.accept()
        self.logger.info("Accepted connection from %s", address)
        self.clients.append( MainServerClient(connection, address) )
        self.poll.register(connection.fileno(), select.POLLIN)        
        return

    def close_client(self, sock):
        sock.close()
        return
        
    def remove_client(self, sock):
        found = False
        for i in range(len(self.clients)):
            if self.clients[i].sock == sock:
                found = True
                break
        if found:
            entry = self.clients.pop(i)
        if sock:
            try:
                self.poll.unregister(sock.fileno())
            except socket.error as e:
                self.logger.error("remove_client:socket.error: %s; found=%s i=%s", e, str(found), str(i))
            except:
                self.logger.error("remove_client:Unknown exception: %s", sys.exc_info()[0])
        return

    def send_client_socket_message(self, sock, msg):
        """Send a message to a remote client."""
        
        try:
            gc = GameComm(sock)
            if not gc.write_mesg(msg):
                self.logger.error("Error writing message: %s", msg)
        except:
            self.logger.error("Error in send_client_socket_message.")
            raise

        return
        
    def receive_client_socket_message(self, client_index):
        """Receive messages from a remote client."""

        client = self.clients[client_index]
        sock = client.sock
        self.logger.debug('receive_client_socket_message')
        if not sock:
            self.logger.error('receive_client_socket_message: done (sock=None)')
            return
            
        try:
            msg = None
            gc = GameComm(sock)
            msg = gc.read_mesg()
            self.logger.debug("sock.recv(): %s", msg)
        except socket.error as e:
            self.logger.error("sock[%d] closed on recv: %s", client_index, e)
            self.remove_client(sock) # remove needs sock.fileno(), close afterwards
            self.close_client(sock)
        except:
            self.logger.error("receive_client_socket_message:Unknown exception %s", sys.exc_info()[0])
            raise

        if msg:
            code = msg.get_command()
            if code == M_CLOSED:
                self.remove_client(sock)
            elif code == M_LOGIN:
                if msg.get_request():
                    rmsg = GameMessageLogin()
                    rmsg.set_request(False)
                    rmsg.set_result(True)
                    rmsg.set_user(msg.get_user())
                    self.clients[client_index].name = msg.get_user()
                    self.send_client_socket_message(sock, rmsg)
                    self.clients[client_index].state = MS_STATE_LOGGED_IN
                    self.logger.info("Logged in %s", msg.get_user())
                else:
                    self.logger.error("Unexpected non-request login message: %s", msg)
            elif code == M_REQUEST_DUAL:
                rmsg = WaitForDualMessage()
                self.send_client_socket_message(sock, rmsg)
                self.clients[client_index].state = MS_STATE_WAIT_DUAL_GAME
                self.logger.info("Dual Requested")
                self.spawn_dual_game()
            elif code == M_REQUEST_SINGLE:
                rmsg = WaitForSingleMessage()
                self.send_client_socket_message(sock, rmsg)
                self.clients[client_index].state = MS_STATE_WAIT_SINGLE_GAME
                self.logger.info("Single Requested")
                self.spawn_single_game()
            elif code == M_REQUEST_TOURNAMENT:
                self.tournament.add_player(self.clients[client_index].name)
                eligible_players = self.tournament.get_eligible_players()
                if self.clients[client_index].name in eligible_players:
                    rmsg = WaitForTournamentMessage()
                    self.send_client_socket_message(sock, rmsg)
                    self.clients[client_index].state = MS_STATE_WAIT_TOURNAMENT_GAME
                    self.logger.info("Tournament Requested")
                    self.spawn_tournament_game()
                else:
                    rmsg = WaitForDualMessage()
                    self.send_client_socket_message(sock, rmsg)
                    self.clients[client_index].state = MS_STATE_WAIT_DUAL_GAME
                    self.logger.info("Tournament Requested -> Dual Offered for %s", self.clients[client_index].name)
                    self.spawn_dual_game()
            elif code == M_REQUEST_AI:
                rmsg = WaitForAiMessage()
                self.send_client_socket_message(sock, rmsg)
                self.clients[client_index].state = MS_STATE_AI_PLAYER
                self.logger.info("AI Requested")
                self.spawn_single_game()
            elif code == M_REQUEST_VIEW:
                rmsg = WaitForViewMessage()
                self.send_client_socket_message(sock, rmsg)
                self.clients[client_index].state = MS_STATE_VIEWER
                self.logger.info("View Requested")
            elif code in ALL_MESSAGE_CODES:
                self.logger.error("Unexpected message in main server, thowing it away. (%s)" , msg)
            elif code == M_EAGAIN:
                self.logger.debug("Waiting to try again.")
            else:
                self.logger.error("Unexpected cmd: %s", code)

        self.logger.debug('receive_client_socket_message: done')
        return

    def handle_client(self, fd):
        for i in range(len(self.clients)):
            client = self.clients[i]
            if client.sock.fileno() == fd:
                self.receive_client_socket_message(i)
                return True
        return False
        
    def run(self):
        """Accepts pairs of connections, then spawns a process to handle them."""
        self.logger.debug('run')

        try:
            self.prepare_socket()
            self.prepare_poll()
            while not self.done:
                ready_list = self.poll.poll()
                for(fd, event) in ready_list:
                    if self.sock and self.sock.fileno() == fd:
                        self.accept_new_client()
                    elif self.handle_client(fd):
                        pass
                    else:
                        self.logger.error("Unexpected fd: %d, unregistering from poll", fd)
                        self.poll.unregister(fd)
                self.join_processes()
        except:
            self.close_socket()
            raise
                    
        self.logger.debug('run finished')
        return


def main():
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
    server = MainServer()
    server.run()
    return

if __name__ == "__main__":
    main()

