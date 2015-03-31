from common.wall import WallData
from object import Object
from config import *

class Wall(Object):

    def __init__(self, x, y, w, h):
        # don't call base class constructor, because
        # data is initialized here
        self.data = WallData(x, y, w, h)
        self.data.set_health(HEALTH_WALL)
        self.data.set_max_health(HEALTH_WALL)
        self.assign_object_id()
        self.hit_oid = -1   # the oid of the object we hit
        return

    def evolve(self, engine, boxes, dt, min_size):
        # walls don't move, so override the method
        return

