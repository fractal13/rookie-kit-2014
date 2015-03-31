import random
from common.npc import NPCData
from object import Object
from config import *

class NPC(Object):

    def __init__(self, x, y, w, h):
        # don't call base class constructor, because
        # data is initialized here
        self.data = NPCData(x, y, w, h)
        self.data.set_health(HEALTH_NPC)
        self.data.set_max_health(HEALTH_NPC)
        self.assign_object_id()
        self.hit_oid = -1   # the oid of the object we hit
        
        self.move_time      = 0.0
        self.min_move_time  = 3.0
        self.move_chance    = 0.01
        return

    def evolve(self, engine, boxes, dt, min_size):
        self.move_time += dt
        if (self.move_time >= self.min_move_time and
            random.random() < self.move_chance):
            degrees = random.random() * 360.
            speed   = 20.0
            self.set_direction_degrees(degrees)
            self.set_speed(speed)
            self.move_time = 0.0
        Object.evolve(self, engine, boxes, dt, min_size)
        return
        
