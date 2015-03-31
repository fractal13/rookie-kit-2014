import sys, select, random, time, math
from common.game_comm import *
from engine_client.game_engine import ClientGameEngine
from client.client_game_socket import ClientGameSocket
import engine_client.game_engine as game_engine

def dist(obj1, obj2):
    x1 = obj1.get_x() + obj1.get_w()/2.
    y1 = obj1.get_y() + obj1.get_h()/2.
    x2 = obj2.get_x() + obj2.get_w()/2.
    y2 = obj2.get_y() + obj2.get_h()/2.

    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx*dx + dy*dy)

def direction(obj1, obj2):
    x1 = obj1.get_x() + obj1.get_w()/2.
    y1 = obj1.get_y() + obj1.get_h()/2.
    x2 = obj2.get_x() + obj2.get_w()/2.
    y2 = obj2.get_y() + obj2.get_h()/2.
    dx = x2 - x1
    dy = y2 - y1
    return math.degrees(math.atan2(dy, dx))

class AiClient:
    """
    This class plays the game
    """

    def __init__(self, name, server_host="localhost", server_port=20149):
        self.server_host = server_host
        self.server_port = server_port
        self.name = name
        self.read_list = []
        self.server_host = server_host
        self.server_port = server_port
        self.client_game_socket = ClientGameSocket(self.read_list, self.server_host, self.server_port)
        self.engine = None
        self.poll_time = .25
        self.do_ai = False
        return

    def set_ai(self, value):
        self.do_ai = value
        return

    def get_sock(self):
        return self.client_game_socket.get_sock()
        
    def set_engine(self, engine):
        self.engine = engine
        return
        
    def connect_to_server(self):
        self.client_game_socket.connect_to_server()
        return

    def disconnect_from_server(self):
        self.client_game_socket.disconnect_from_server()
        return
        
    def socket_is_ready(self):
        rds, wrs, xs = select.select(self.read_list, [], [], 0.0)
        for fd in rds:
            if self.client_game_socket.is_ready(fd):
                return True
        return False

    def generate_external_events(self):
        if self.engine:
            # receive incoming messages
            while self.socket_is_ready():
                self.client_game_socket.process_event(self.engine)
            # send outgoing messages
            self.client_game_socket.send_messages(self.engine)
        return
        
    def new_game(self):
        if self.do_ai:
            mode = game_engine.MODE_AI
        else:
            mode = game_engine.MODE_DUAL
        self.set_engine(ClientGameEngine(self.name, mode))
        self.disconnect_from_server()
        self.connect_to_server()
        return

    def shooting_solution(self, engine):
        data = engine.get_data()
        myoid = engine.get_player_oid()
        me    = data.get_object(myoid)
        if not me: return
        objects = data.get_objects()

        closest = None
        closest_d = 1000.
        for oid in objects:
            obj = objects[oid]
            if obj != me and dist(me, obj) < closest_d:
                if obj.is_alive() and (obj.is_npc() or obj.is_player()):
                    closest_d = dist(me, obj)
                    closest = obj
        if closest_d < 100.:
            degrees = direction(me, closest)
            engine.set_missile_range_short()
            engine.set_missile_direction(degrees)
            engine.fire_missile()
        return

    def moving_solution(self, engine):
        data = engine.get_data()
        myoid = engine.get_player_oid()
        me    = data.get_object(myoid)
        if not me: return
        objects = data.get_objects()

        closest = None
        closest_d = 1000.
        for oid in objects:
            obj = objects[oid]
            if obj != me and dist(me, obj) < closest_d:
                if obj.is_alive() and (obj.is_npc() or obj.is_player()):
                    closest_d = dist(me, obj)
                    closest = obj
        if closest_d < 1000. and closest_d > 40.:
            degrees = direction(me, closest)
            engine.set_player_direction(degrees)
            engine.set_player_speed_slow()
        elif closest_d <= 40.:
            engine.set_player_speed_stop()
        return
        
        
    def act(self, engine):
        self.shooting_solution(engine)
        self.moving_solution(engine)
        return

    def main_loop(self):
        self.new_game()

        sock = self.get_sock()
        t0 = time.time()
        while self.engine.get_data().get_winner_name() == "":
            rds, wrs, xs = select.select(self.read_list, [], [], self.poll_time)
            for fd in rds:
                if fd == sock.fileno():
                    self.client_game_socket.process_event(self.engine)
                else:
                    print "Unexpected fd", fd, sock.fileno()
            t1 = time.time()
            if t1 - t0 >= 1.:
                self.act(self.engine)
                self.client_game_socket.send_messages(self.engine)
                t0 = t1
        return
        
