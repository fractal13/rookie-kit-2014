import random
from player import Player
from wall import Wall
from npc import NPC
from missile import Missile
from config import *
from common.event import *

class GameEngine:

    def __init__(self):
        self.new_game()
        return

    def place_one_npc(self):
        """
        Randomly place npc object until it doesn't collide with any existing objects
        """
        
        done = False
        while not done:
            x = random.randrange(self.npc_width, self.width - self.npc_width, self.npc_width)
            y = random.randrange(self.npc_height, self.height - self.npc_height, self.npc_height)
            npc = NPC(x, y, self.npc_width, self.npc_height)
            
            found = False
            for oid in self.all_objects:
                if npc.collide(npc.get_x(), npc.get_y(), self.all_objects[oid]):
                    found = True
            if not found:
                done = True
        return npc
        
    def make_npcs(self):
        for i in range(self.num_npcs):
            npc = self.place_one_npc()
            self.add_npc(npc)
        return

    def place_one_wall(self):
        """
        Randomly place wall object until it doesn't collide with any existing objects
        """
        
        done = False
        while not done:
            x = random.randrange(self.wall_thick, self.width - self.wall_thick, self.wall_thick)
            y = random.randrange(self.wall_thick, self.height - self.wall_thick, self.wall_thick)
            wall = Wall(x, y, self.wall_thick, self.wall_thick)
            
            found = False
            for oid in self.all_objects:
                if wall.collide(wall.get_x(), wall.get_y(), self.all_objects[oid]):
                    found = True
            if not found:
                done = True
        return wall
        
    def make_walls(self):
        # top
        wall = Wall(0, 0, self.width, self.wall_thick)
        self.add_wall(wall)
        # bottom
        wall = Wall(0, self.height-self.wall_thick, self.width, self.wall_thick)
        self.add_wall(wall)
        # left 
        wall = Wall(0, 0, self.wall_thick, self.height)
        self.add_wall(wall)
        # right
        wall = Wall(self.width-self.wall_thick, 0, self.wall_thick, self.height)
        self.add_wall(wall)
        
        # random walls
        for i in range(self.num_walls):
            wall = self.place_one_wall()
            self.add_wall(wall)
        return

    def place_one_player(self):
        """
        Randomly place player object until it doesn't collide with any existing objects
        """
        
        done = False
        while not done:
            player = Player(random.randrange(self.player_width, self.width-2*self.player_width),
                            random.randrange(self.player_height, self.height-2*self.player_height),
                            self.player_width,
                            self.player_height)
            found = False
            for oid in self.all_objects:
                if player.collide(player.get_x(), player.get_y(), self.all_objects[oid]):
                    found = True
            if not found:
                done = True
        return player
        
    def place_players(self):
        # add each player as created, so the next player's creation can use collision detection
        player1 = self.place_one_player()
        self.add_player(player1)
        player2 = self.place_one_player()
        self.add_player(player2)
        self.player_oid = [ player1.get_object_id(),
                            player2.get_object_id() ]
        for oid in self.player_oid:
            self.set_missile_range_short(oid)
            self.set_missile_power_low(oid)
        return
        
    def new_game(self):
        self.player_width   = PLAYER_WIDTH
        self.player_height  = PLAYER_HEIGHT
        self.wall_thick     = WALL_THICK
        self.num_walls      = NUM_WALLS
        self.npc_width      = NPC_WIDTH
        self.npc_height     = NPC_HEIGHT
        self.num_npcs       = NUM_NPCS
        self.missile_width  = MISSILE_WIDTH
        self.missile_height = MISSILE_HEIGHT
        self.minimum_size   = min( (self.player_width, self.player_height, self.wall_thick,
                                    self.npc_width, self.npc_height,
                                    self.missile_width, self.missile_height) )
        self.width          = FIELD_WIDTH
        self.height         = FIELD_HEIGHT
        self.players        = {}
        self.npcs           = {}
        self.missiles       = {}
        self.walls          = {}
        self.all_objects    = {}
        self.events         = []
        self.make_walls()
        self.place_players()
        self.make_npcs()
        self.winner_oid = -1  # no winner yet
        self.game_over_flag = False
        self.game_over_percent = 0.0
        self.total_time = 0.0 #
        self.max_total_time = 30. * 60. # 30 minutes
        return

    def add_player(self, p):
        oid = p.get_object_id()
        self.players[oid] = p
        self.all_objects[oid] = p
        return
        
    def add_wall(self, w):
        oid = w.get_object_id()
        self.walls[oid] = w
        self.all_objects[oid] = w
        return

    def add_npc(self, n):
        oid = n.get_object_id()
        self.npcs[oid] = n
        self.all_objects[oid] = n
        return
        
    def add_missile(self, m):
        oid = m.get_object_id()
        self.missiles[oid] = m
        self.all_objects[oid] = m
        return

    def check_game_over(self):
        alive_count = 0
        alive_oid   = -1
        for oid in self.players:
            if self.players[oid].is_alive():
                alive_count += 1
                alive_oid = oid
        if ((alive_count < 2) or
            (self.total_time > self.max_total_time)):
            self.game_over_flag = True
            self.game_over_percent = 0.0
        if alive_count == 1:
            self.winner_oid = alive_oid
        return

    def handle_missile_on_wall_collision(self, moid, ooid):
        """missile(moid) collides with wall(ooid) object"""
        
        if self.all_objects[moid].is_alive() and self.all_objects[ooid].is_alive():
            # both objects are alive, kill the missile
            d1 = self.all_objects[moid].apply_damage(INFINITE_HEALTH)
            self.add_missile_hit_event(self.all_objects[moid], self.all_objects[ooid])
        return
        
    def handle_missile_on_other_collision(self, moid, ooid):
        """missile(moid) collides with other(ooid) object"""
        
        if self.all_objects[moid].is_alive() and self.all_objects[ooid].is_alive():
            # both objects are alive, damage both objects
            damage = self.all_objects[moid].get_power()
            d1 = self.all_objects[moid].apply_damage(damage)
            d2 = self.all_objects[ooid].apply_damage(damage)
            self.add_missile_hit_event(self.all_objects[moid], self.all_objects[ooid])
            if self.all_objects[ooid].get_health() < EPSILON and ooid in self.players:
                self.set_missile_power_none(ooid)
                self.set_missile_range_none(ooid)
                self.set_player_speed_stop(ooid)
            # experience based on damage caused
            poid = self.all_objects[moid].get_player_oid()
            self.all_objects[poid].add_experience(d2)
        return
            
    def handle_missile_on_missile_collision(self, moid, ooid):
        """missile(moid) collides with missile(ooid) object"""
        
        if self.all_objects[moid].is_alive() and self.all_objects[ooid].is_alive():
            # both objects are alive, damage both objects
            damage = self.all_objects[moid].get_power()
            d1 = self.all_objects[moid].apply_damage(damage)
            d2 = self.all_objects[ooid].apply_damage(damage)
            self.add_missile_hit_event(self.all_objects[moid], self.all_objects[ooid])
            self.add_missile_hit_event(self.all_objects[ooid], self.all_objects[moid])
            # experience based on damage caused
            poid = self.all_objects[moid].get_player_oid()
            self.all_objects[poid].add_experience(d2)
            poid = self.all_objects[ooid].get_player_oid()
            self.all_objects[poid].add_experience(d1)
        return
        
    def handle_collision(self, oid1, oid2):
        if not oid1 in self.all_objects:
            print "Oops, oid1 %d doesn't exist" % (oid1)
            return
        if not oid2 in self.all_objects:
            print "Oops, oid2 %d doesn't exist" % (oid2)
            return
        if (str(self.all_objects[oid1].__class__) == "engine_server.missile.Missile" and
            str(self.all_objects[oid2].__class__) == "engine_server.missile.Missile"):
            # oid1 = missile and oid2 = missile
            self.handle_missile_on_missile_collision(oid1, oid2)
        elif str(self.all_objects[oid1].__class__) == "engine_server.missile.Missile":
            # oid1 = missile 
            if str(self.all_objects[oid2].__class__) != "engine_server.wall.Wall":
                self.handle_missile_on_other_collision(oid1, oid2)
            else:
                self.handle_missile_on_wall_collision(oid1, oid2)
        elif str(self.all_objects[oid2].__class__) == "engine_server.missile.Missile":
            # oid2 = missile
            if str(self.all_objects[oid1].__class__) != "engine_server.wall.Wall":
                self.handle_missile_on_other_collision(oid2, oid1)
            else:
                self.handle_missile_on_wall_collision(oid2, oid1)
        else:
            # no missile involved
            pass
        return
        
    def evolve(self, dt):
        self.total_time += dt
        if self.game_over_flag:
            self.game_over_percent += dt/GAME_OVER_TIME
            # let dying objects die
            for oid in self.all_objects:
                if self.all_objects[oid].is_dying():
                    self.all_objects[oid].add_dying_percent(dt)
            # nothing else
            return

        # if player has quit, kill them
        for oid in self.players:
            if self.players[oid].get_quit():
                self.players[oid].apply_damage(self.players[oid].get_health()+1.)
                self.set_missile_power_none(oid)
                self.set_missile_range_none(oid)
                self.set_player_speed_stop(oid)
                
        # evolve each object
        for oid in self.all_objects:
            self.all_objects[oid].evolve(self, self.all_objects, dt, self.minimum_size)
            
        # check for collisions, and apply results
        for oid in self.all_objects:
            hit_oid = self.all_objects[oid].hit_oid
            if hit_oid > 0:
                self.handle_collision(oid, hit_oid)
                
        # throw out the dead, but only if not changed this round
        # allows dead objects to be removed from client
        dead_oid = []
        for oid in self.all_objects:
            if self.all_objects[oid].is_dead() and not self.all_objects[oid].is_changed():
                dead_oid.append(oid)
        for oid in dead_oid:
            self.delete_object(oid)
            
        # spawn
        while len(self.npcs) < self.num_npcs:
            npc = self.place_one_npc()
            self.add_npc(npc)

        self.check_game_over()
        return

    def delete_object(self, oid):
        name = str(self.all_objects[oid].__class__)
        del self.all_objects[oid]
        if name == "engine_server.player.Player":
            del self.players[oid]
        elif name == "engine_server.npc.NPC":
            del self.npcs[oid]
        elif name == "engine_server.missiles.Missile":
            del self.missiles[oid]
        elif name == "engine_server.wall.Wall":
            del self.walls[oid]
        return
        
    def get_changed_objects(self):
        objs = []
        for oid in self.all_objects:
            if self.all_objects[oid].is_changed():
                objs.append(self.all_objects[oid])
        return objs

    def clear_changed_objects(self):
        for oid in self.all_objects:
            self.all_objects[oid].clear_changed()
        return

    def get_events(self):
        return self.events

    def clear_events(self):
        self.events = []
        return

    def add_missile_fire_event(self, m):
        self.events.append(MissileFireEvent(m.get_player_oid(), m.get_object_id(), m.get_range(), m.get_power()))
        return
    def add_missile_misfire_event(self, oid):
        self.events.append(MissileMisfireEvent(oid))
        return
    def add_missile_hit_event(self, m, t):
        self.events.append(MissileHitEvent(m.get_player_oid(), m.get_object_id(), t.get_object_id()))
        return
    def add_missile_dying_event(self, m):
        self.events.append(MissileDyingEvent(m.get_player_oid(), m.get_object_id()))
        return

    def game_over(self):
        return self.game_over_percent >= 1.0

    def get_game_over_percent(self):
        return self.game_over_percent

    def get_winner_oid(self):
        return self.winner_oid

    def __str__(self):
        first = True
        s = ""
        for oid in self.all_objects:
            if not first:
                s += "\n"
            s += str(self.all_objects[oid])
            first = False
        return s

    #
    # player methods
    #

    # find oid
    def get_player1_oid(self):
        return self.player_oid[0]
    def get_player2_oid(self):
        return self.player_oid[1]
        
    # set speed
    def set_player_speed_stop(self, oid):
        self.players[oid].set_speed(PLAYER_SPEED_STOP)
        return
    def set_player_speed_slow(self, oid):
        if not self.players[oid].is_alive(): return
        self.players[oid].set_speed(PLAYER_SPEED_SLOW)
        return
    def set_player_speed_medium(self, oid):
        if not self.players[oid].is_alive(): return
        self.players[oid].set_speed(PLAYER_SPEED_MEDIUM)
        return
    def set_player_speed_fast(self, oid):
        if not self.players[oid].is_alive(): return
        self.players[oid].set_speed(PLAYER_SPEED_FAST)
        return

    # set direction
    def set_player_direction(self, oid, degrees):
        if not self.players[oid].is_alive(): return
        self.players[oid].set_direction_degrees(degrees)
        return
        
    # set missile range
    def set_missile_range_none(self, oid):
        self.players[oid].set_missile_range(MISSILE_RANGE_NONE)
        return
    def set_missile_range_short(self, oid):
        if not self.players[oid].is_alive(): return
        self.players[oid].set_missile_range(MISSILE_RANGE_SHORT)
        return
    def set_missile_range_medium(self, oid):
        if not self.players[oid].is_alive(): return
        self.players[oid].set_missile_range(MISSILE_RANGE_MEDIUM)
        return
    def set_missile_range_long(self, oid):
        if not self.players[oid].is_alive(): return
        self.players[oid].set_missile_range(MISSILE_RANGE_LONG)
        return
        
    # set missile direction
    def set_missile_direction(self, oid, degrees):
        if not self.players[oid].is_alive(): return
        self.players[oid].set_missile_direction_degrees(degrees)
        return
        
    # set missile power
    def set_missile_power_none(self, oid):
        self.players[oid].set_missile_power(MISSILE_POWER_NONE)
        return
    def set_missile_power_low(self, oid):
        if not self.players[oid].is_alive(): return
        self.players[oid].set_missile_power(MISSILE_POWER_LOW)
        return
    def set_missile_power_medium(self, oid):
        if not self.players[oid].is_alive(): return
        self.players[oid].set_missile_power(MISSILE_POWER_MEDIUM)
        return
    def set_missile_power_high(self, oid):
        if not self.players[oid].is_alive(): return
        self.players[oid].set_missile_power(MISSILE_POWER_HIGH)
        return
        
    # fire missile
    def fire_missile(self, oid):
        if not self.players[oid].is_alive(): return
        dx = self.players[oid].get_missile_dx()
        dy = self.players[oid].get_missile_dy()
        mrange = self.players[oid].get_missile_range()
        power = self.players[oid].get_missile_power()
        if mrange < EPSILON or power < EPSILON:
            self.add_missile_misfire_event(oid)
            return

        (x, y) = self.players[oid].get_edge_point(dx, dy, self.missile_width, self.missile_height)
        
        m = Missile(x, y, self.missile_width, self.missile_height, mrange, power, oid)
        m.set_direction(dx, dy)
        m.set_speed(MISSILE_SPEED)
        if m and self.players[oid].consume_missile_mana(m.get_mana_cost()):
            self.add_missile(m)
            self.add_missile_fire_event(m)
        else:
            self.add_missile_misfire_event(oid)
        return

    # player disconnected
    def set_player_disconnected(self, oid):
        self.players[oid].set_quit()
        return
