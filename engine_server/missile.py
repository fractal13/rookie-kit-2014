import random, math
from common.missile import MissileData
from object import Object
from config import *

class Missile(Object):

    def __init__(self, x, y, w, h, mrange, power, player_oid):
        # don't call base class constructor, because
        # data is initialized here
        self.data = MissileData(x, y, w, h)
        self.assign_object_id()
        self.hit_oid = -1   # the oid of the object we hit
        self.data.set_range(mrange)
        self.data.set_power(power)
        self.data.set_health(HEALTH_MISSILE)
        self.data.set_max_health(HEALTH_MISSILE)
        self.data.set_player_oid(player_oid)
        self.data.set_hit_max_range(False)
        return

    def get_range(self):
        return self.data.get_range()

    def get_power(self):
        return self.data.get_power()

    def get_player_oid(self):
        return self.data.get_player_oid()

    def get_mana_cost(self):
        return MISSILE_MANA_COST_RATE * math.log(self.data.get_range()) * math.log(10.*self.data.get_power())

    def evolve(self, engine, boxes, dt, min_size):
        Object.evolve(self, engine, boxes, dt, min_size)
        if self.data.get_distance() > self.get_range() and self.is_alive():
            self.set_dying()
            self.data.set_hit_max_range(True)
            engine.add_missile_dying_event(self)
        return
        
