from multiprocessing import Process, Pipe
import time, random, sys, socket, select
import logging
from main_server_client import *
from tournament import Tournament
from common.game_comm import *
from common.object_message import *
from common.command_message import *
from common.event_message import *
from engine_server.game_engine import GameEngine
from engine_server.player import Player
from engine_server.wall import Wall
from engine_server.npc import NPC
from engine_server.missile import Missile
from engine_server.config import EPSILON

class GameServer:
    """
    Game class that receives and sends communications
    from and to 2 separate client pipes.  It will
    sleep to achieve a desired frame rate.  Each
    client incoming pipe will be emptied each frame.
    """

    def __init__(self, pipe1, pipe2, client1, client2, pipe3, viewer):
        self.logger = logging.getLogger('GameServer')
        self.logger.debug('__init__')
        self.pipe = [ pipe1, pipe2 ]
        self.clients = [ client1, client2 ]
        if viewer and pipe3:
            self.pipe.append(pipe3)
            self.clients.append(viewer)
        self.done = False
        self.sent_winner = False
        self.time   = 0.
        self.frame_rate = 30.
        self.desired_dt = 1.0/float(self.frame_rate)
        self.engine = GameEngine()
        self.tournament = Tournament()
        self.tournament.open()
        return

    def end_tournament_game(self, winner):
        if self.tournament.either_game_exists(self.clients[0].name, self.clients[1].name):
            self.tournament.end_game(self.clients[0].name, self.clients[1].name, winner)
        return
        
    def start_tournament_game(self):
        if self.tournament.either_game_exists(self.clients[0].name, self.clients[1].name):
            self.tournament.start_game(self.clients[0].name, self.clients[1].name)
        return
        
    def evolve(self, dt):
        """Evolve the state of the system dt into the future."""
        self.logger.debug('evolve')
        self.time += dt
        self.engine.evolve(dt)
        if self.engine.game_over():
            self.done = True
        count = 0
        for pid in range(len(self.pipe)):
            if self.pipe[pid] and self.clients[pid].state != MS_STATE_VIEWER:
                count += 1
        if count == 0:
            self.done = True
        return

        
    def close_pipe(self, pid):
        if self.pipe[pid]:
            self.pipe[pid].close()
            self.pipe[pid] = None
        return
        
    def close_pipes(self):
        for pid in range(len(self.pipe)):
            self.close_pipe(pid)
        return

    def oid_from_pid(self, pid):
        if pid == 0 or pid == 2: # viewer == 2
            oid = self.engine.get_player1_oid()
        else:
            oid = self.engine.get_player2_oid()
        return oid

    def process_message(self, pid, msg):

        self.logger.debug("process_message(pipe[%d]) %s", pid, msg)
        code = msg.get_command()
        if code == M_CLOSED:
            self.logger.debug("pipe[%d] closed on M_CLOSED", pid)
            oid = self.oid_from_pid(pid)
            self.engine.set_player_disconnected(oid)
            self.close_pipe(pid)
        elif code == M_ECHO:
            rmsg = GameMessageEcho()
            rmsg.set_text(msg.get_text())
            self.logger.debug("pipe[%d].send(): %s" , pid, rmsg)
            if self.pipe[pid] and pid < 2:
                self.pipe[pid].send(rmsg)
        elif code == M_BROADCAST:
            rmsg = GameMessageBroadcast()
            rmsg.set_text(msg.get_text())
            if pid < 2:
                for i in range(len(self.pipe)):
                    self.logger.debug("pipe[%d].send(): %s" , i, rmsg)
                    if self.pipe[i]:
                        self.pipe[i].send(rmsg)
        elif code == M_REQUEST_PLAYER_OID:
            oid = self.oid_from_pid(pid)
            rmsg = PlayerOidMessage(oid)
            if self.pipe[pid]:
                self.pipe[pid].send(rmsg)
        elif code == M_SET_PLAYER_SPEED:
            if pid < 2:
                speed = msg.get_speed()
                oid = self.oid_from_pid(pid)
                if speed == T_SPEED_STOP:
                    self.engine.set_player_speed_stop(oid)
                elif speed == T_SPEED_SLOW:
                    self.engine.set_player_speed_slow(oid)
                elif speed == T_SPEED_MEDIUM:
                    self.engine.set_player_speed_medium(oid)
                elif speed == T_SPEED_FAST:
                    self.engine.set_player_speed_fast(oid)
                else:
                    self.logger.error("Unexpected speed %s", speed)
        elif code == M_SET_PLAYER_DIRECTION:
            if pid < 2:
                degrees = msg.get_degrees()
                oid = self.oid_from_pid(pid)
                self.engine.set_player_direction(oid, degrees)
        elif code == M_SET_MISSILE_RANGE:
            if pid < 2:
                mrange = msg.get_range()
                oid = self.oid_from_pid(pid)
                if mrange == T_RANGE_NONE:
                    self.engine.set_missile_range_none(oid)
                elif mrange == T_RANGE_SHORT:
                    self.engine.set_missile_range_short(oid)
                elif mrange == T_RANGE_MEDIUM:
                    self.engine.set_missile_range_medium(oid)
                elif mrange == T_RANGE_LONG:
                    self.engine.set_missile_range_long(oid)
                else:
                    self.logger.error("Unexpected range %s", mrange)
        elif code == M_SET_MISSILE_DIRECTION:
            if pid < 2:
                degrees = msg.get_degrees()
                oid = self.oid_from_pid(pid)
                self.engine.set_missile_direction(oid, degrees)
        elif code == M_SET_MISSILE_POWER:
            if pid < 2:
                power = msg.get_power()
                oid = self.oid_from_pid(pid)
                if power == T_POWER_NONE:
                    self.engine.set_missile_power_none(oid)
                elif power == T_POWER_LOW:
                    self.engine.set_missile_power_low(oid)
                elif power == T_POWER_MEDIUM:
                    self.engine.set_missile_power_medium(oid)
                elif power == T_POWER_HIGH:
                    self.engine.set_missile_power_high(oid)
                else:
                    self.logger.error("Unexpected power %s", power)
        elif code == M_FIRE_MISSILE:
            if pid < 2:
                oid = self.oid_from_pid(pid)
                self.engine.fire_missile(oid)
        else:
            self.logger.error('Unknown message: %s', code)
            
        return
        
    def process_pipe(self, pid):
        """Receive all messages in a pipe and process them."""

        self.logger.debug('process_pipe(%d)', pid)
        try:
            while self.pipe[pid] and self.pipe[pid].poll():
                msg = self.pipe[pid].recv()
                self.logger.debug("pipe[%d].recv(): %s" , pid, msg)
                self.process_message(pid, msg)
        except EOFError as e:
            self.logger.error("pipe[%d] closed on recv: %s", pid, e)
            oid = self.oid_from_pid(pid)
            self.engine.set_player_disconnected(oid)
            self.close_pipe(pid)
        except:
            self.logger.error("pipe[%d] closed on recv: %s", pid, sys.exc_info()[0])
            oid = self.oid_from_pid(pid)
            self.engine.set_player_disconnected(oid)
            self.close_pipe(pid)
            raise
        return

    def receive_messages(self):
        """Receive messages from clients."""

        self.logger.debug('receive_messages')
        pids = range(len(self.pipe))
        # randomize order for fairness
        random.shuffle(pids)
        for pid in pids:
            self.process_pipe(pid)
        return

    def get_object_messages(self, objs):
        msgs = []
        for obj in objs:
            if isinstance(obj, Player):
                msg = PlayerUpdateMessage(obj.get_data())
            elif isinstance(obj, Wall):
                msg = WallUpdateMessage(obj.get_data())
            elif isinstance(obj, NPC):
                msg = NPCUpdateMessage(obj.get_data())
            elif isinstance(obj, Missile):
                msg = MissileUpdateMessage(obj.get_data())
            else:
                self.logger.error("Unknown object type: %s", obj)
                continue
            msgs.append(msg)
        return msgs

    def get_event_messages(self, events):
        msgs = []
        for event in events:
            msg = event_to_message(event)
            if not msg:
                self.logger.error("Unknown event type: %s %s", event.get_kind(), event)
                continue
            msgs.append(msg)
        return msgs
        
    def send_messages(self):
        """Send update messages back to clients."""
        
        self.logger.debug('send_messages')
        # randomize order for fairness
        pids = range(len(self.pipe))
        random.shuffle(pids)

        # object update messages
        objs = self.engine.get_changed_objects()
        msgs = self.get_object_messages(objs)
        self.engine.clear_changed_objects()
        
        # event messages
        events = self.engine.get_events()
        emsgs = self.get_event_messages(events)
        self.engine.clear_events()
        msgs.extend(emsgs)

        # game over message
        if self.engine.get_game_over_percent() > EPSILON and not self.sent_winner:
            oid = self.engine.get_winner_oid()
            wname = ""
            for pid in pids:
                if oid == self.oid_from_pid(pid) and pid < 2:
                    wname = self.clients[pid].name
            msg = GameOverMessage(wname)
            msgs.append(msg)
            print "Winner is %s" % (wname)
            self.end_tournament_game(wname)
            self.sent_winner = True
            
        for pid in pids:
            try:
                for msg in msgs:
                    self.logger.debug("pipe[%d].send(%s)", pid, msg)
                    if self.pipe[pid]:
                        self.pipe[pid].send(msg)
                if self.done:
                    msg = GameMessageClosed()
                    self.logger.debug("pipe[%d].send(%s)", pid, msg)
                    if self.pipe[pid]:
                        self.pipe[pid].send(msg)
            except ValueError as e:
                self.logger.error("pipe[%d] closed on send: %s", pid, str(e))
                oid = self.oid_from_pid(pid)
                self.engine.set_player_disconnected(oid)
                self.close_pipe(pid)
            except:
                self.logger.error("pipe[%d] closed on send: %s", pid, sys.exc_info()[0])
                oid = self.oid_from_pid(pid)
                self.engine.set_player_disconnected(oid)
                self.close_pipe(pid)
                raise
        return

    def run(self):
        """Run one game."""
        
        self.logger.info('run')
        self.start_tournament_game()
        t1 = t0 = time.time()
        while not self.done:
            # receive messages from clients
            self.receive_messages()
            # enforce frame-rate
            dt = time.time() - t1
            if dt < self.desired_dt:
                time.sleep(self.desired_dt - dt)
            t2 = time.time()
            dt = t2 - t1
            # advance game state
            self.evolve(dt)
            # send messages to clients
            self.send_messages()
            t1 = t2

        t1 = time.time()
        self.logger.info("run done. self.time: %f  t1-t0: %f", self.time, t1 - t0)
        self.close_pipes()
        return

class GameClientConnection:
    """
    Client class that receives and sends communications
    from and to the game via a pipe.  It also receives
    and sends messages from and to the client via
    network communications.
    """

    def __init__(self, cid, sock, pipe):
        self.logger = logging.getLogger('GameClientConnection_%d' % (cid,))
        self.logger.debug('__init__')
        self.cid = cid
        self.sock = sock
        self.pipe = pipe
        self.x = 0
        self.done = False
        self.bad_write_count = 0
        self.max_bad_write_count = 10
        return

    def close_pipe(self):
        if self.pipe:
            self.logger.debug('close_pipe')
            self.poll.unregister(self.pipe.fileno())
            self.pipe.close()
            self.pipe = None
        if self.sock:
            self.close_sock()
        if not (self.sock or self.pipe):
            self.done = True
        return

    def close_sock(self):
        if self.sock:
            self.logger.debug('close_sock')
            self.poll.unregister(self.sock.fileno())
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            self.sock.close()
            self.sock = None
        if self.pipe:
            self.close_pipe()
        if not (self.sock or self.pipe):
            self.done = True
        return
        
    def receive_pipe_messages(self):
        """Receive messages from the game class."""
        
        self.logger.debug('receive_pipe_messages')
        try:
            while self.pipe and self.sock and self.pipe.poll():
                msg = self.pipe.recv()
                self.logger.debug("pipe[%d].recv(): %s" , self.cid, msg)
                code = msg.get_command()
                if code == M_CLOSED:
                    self.logger.debug("pipe[%d] closing pipe", self.cid)
                    self.close_pipe()
                elif code in ALL_MESSAGE_CODES:
                    gc = GameComm(self.sock)
                    if not gc.write_mesg(msg):
                        self.logger.error("Error in write_mesg.")
                        self.bad_write_count += 1
                        if self.bad_write_count >= self.max_bad_write_count:
                            self.logger.error("Too many write errors, closing down.")
                            self.logger.debug("pipe[%d] closing pipe", self.cid)
                            self.close_pipe()
                            self.close_sock()
                    else:
                        self.bad_write_count = 0
                else:
                    self.logger.error("pipe[%d] bad pipe message: %s", self.cid, str(msg))
        except EOFError as e:
            self.logger.error("pipe[%d] closed on recv: %s", self.cid, e)
            self.close_pipe()
        except socket.error as e:
            self.logger.error("sock[%d] closed on send: %s", self.cid, e)
            if self.pipe:
                msg = GameMessageClosed()
                self.pipe.send(msg)
            self.close_sock()
        except:
            self.logger.error("pipe[%d] closed on recv: %s", self.cid, sys.exc_info()[0])
            self.close_pipe()
            raise
            
        return
        
    def receive_socket_messages(self):
        """Receive messages from the remote client."""
        
        self.logger.debug('receive_socket_messages')
        if not self.sock:
            self.logger.error('receive_socket_messages: done (sock=None)')
            return
        if not self.pipe:
            self.logger.error('receive_socket_messages: done (pipe=None)')
            return
            
        try:
            msg = None
            gc = GameComm(self.sock)
            msg = gc.read_mesg()
            self.logger.debug("sock.recv(): %s" , msg)
        except socket.error as e:
            self.logger.error("sock[%d] closed on recv: %s", self.cid, e)
            if self.pipe:
                msg = GameMessageClosed()
                self.pipe.send(msg)
            self.close_sock()
        except:
            self.logger.error("Unknown exeption %s", sys.exc_info()[0])
            raise

        if msg:
            code = msg.get_command()
            if code == M_CLOSED:
                if self.pipe:
                    msg = GameMessageClosed()
                    self.pipe.send(msg)
                self.close_sock()
            elif code in ALL_MESSAGE_CODES:
                if self.pipe:
                    self.logger.debug("pipe.send(%s)" , msg)
                    self.pipe.send(msg)
            elif code == M_EAGAIN:
                self.logger.debug("Waiting to try again.")
            else:
                self.logger.error("Unexpected cmd: %s", code)

        self.logger.debug('receive_socket_messages: done')
        return
        
    def send_pipe_messages(self):
        """Send messages to the game class."""

        self.logger.debug('send_pipe_messages')
        try:
            if self.pipe:
                # self.logger.debug("pipe[%d].send(%s)", self.cid, str(self.x))
                # self.pipe.send(self.x)
                # self.x += 1
                pass
        except ValueError as e:
            self.logger.error("pipe[%d] closed on send: %s", self.cid, str(e))
            self.close_pipe()
        except:
            self.logger.error("pipe[%d] closed on send: %s", self.cid, sys.exc_info()[0])
            self.close_pipe()
            raise
        return
        
    def send_socket_messages(self):
        """Send messages to the remote client."""
        
        self.logger.debug('send_socket_messages')
        return
        
    def run(self):
        """
        Run for one game.
        """

        self.logger.info('run')
        self.poll = select.poll()
        if self.sock:
            self.poll.register(self.sock.fileno(), select.POLLIN)
        if self.pipe:
            self.poll.register(self.pipe.fileno(), select.POLLIN)
        while not self.done:
            self.logger.debug('poll start %d', self.cid)
            ready_list = self.poll.poll()
            self.logger.debug('poll end %d', self.cid)
            for (fd, event) in ready_list:
                if self.sock and self.sock.fileno() == fd:
                    self.receive_socket_messages()
                elif self.pipe and self.pipe.fileno() == fd:
                    self.receive_pipe_messages()
                else:
                    self.logger.error('(%d) Unexpected fd: %d', self.cid, fd)
            self.send_pipe_messages()
            self.send_socket_messages()

        self.logger.info('run done')
        self.close_pipe()
        return

def start_game(pipepair1,pipepair2,client1,client2,pipepair3,viewer0):
    """Global function to launch Game process"""
    # pipepair1[0].close()
    # pipepair2[0].close()
    if viewer0:
        p3 = pipepair3[1]
    else:
        p3 = None
    g = GameServer(pipepair1[1],pipepair2[1],client1,client2,p3,viewer0)
    g.run()
    return
    
def start_client(cid, sock, pipepair1, pipepair2):
    """Global function to launch Client process"""
    # pipepair1[1].close()
    # pipepair2[0].close()
    # pipepair2[1].close()
    c = GameClientConnection(cid, sock, pipepair1[0])
    c.run()
    return

def main(client1,client2,viewer0):
    """Global function to launch the game process,
    and two client managing processes."""
    
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)

    pipe_pair_1 = Pipe()
    pipe_pair_2 = Pipe()
    if viewer0:
        pipe_pair_3 = Pipe()
    else:
        pipe_pair_3 = None
        
    random.random()
    p = Process(target=start_game, args=(pipe_pair_1, pipe_pair_2, client1, client2, pipe_pair_3, viewer0))
    random.random()
    c1 = Process(target=start_client, args=(0, client1.sock, pipe_pair_1, pipe_pair_2, ))
    random.random()
    c2 = Process(target=start_client, args=(1, client2.sock, pipe_pair_2, pipe_pair_1, ))
    random.random()
    if viewer0:
        v0 = Process(target=start_client, args=(2, viewer0.sock, pipe_pair_3, pipe_pair_1, ))
        random.random()
    # pipe_pair_1[0].close()
    # pipe_pair_1[1].close()
    # pipe_pair_2[0].close()
    # pipe_pair_2[1].close()
    p.start()
    c1.start()
    c2.start()
    if viewer0:
        v0.start()
    p.join()
    c1.join()
    c2.join()
    if viewer0:
        v0.join()
    return
    
if __name__ == "__main__":
    main(None, None)

