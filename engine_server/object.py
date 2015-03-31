import math
from common.object import ObjectData
from config import *

class Object:

    next_object_id = 0
    
    def __init__(self, x, y, w, h):
        self.data = ObjectData(x, y, w, h)
        self.data.set_health(HEALTH_OBJECT)
        self.data.set_max_health(HEALTH_OBJECT)
        self.assign_object_id()
        self.hit_oid = -1   # the oid of the object we hit
        return

    def get_object_id(self):
        return self.data.get_oid()
        
    def assign_object_id(self):
        Object.next_object_id += 1
        self.data.set_oid(Object.next_object_id)
        return

    def get_data(self):
        return self.data
    def get_health(self):
        return self.data.get_health()

    def is_changed(self):
        return self.data.changed
        
    def clear_changed(self):
        self.data.changed = False
        return

    def apply_damage(self, damage):
        dh = 0.0
        if self.data.health >= EPSILON:
            if self.data.health >= damage + EPSILON:
                dh = damage
                self.data.health -= damage
            else:
                dh = self.data.health
                self.data.health = 0.0
            self.data.changed = True
            if self.data.health < EPSILON:
                self.data.health = 0.0
                self.set_dying()
        return dh

    def move_until_hit_or_time(self, boxes, tstep, dt, t1):
        keep_x = self.data.x
        keep_y = self.data.y
        keep_t1 = 0
        while t1 < dt + EPSILON:
            if t1 > dt:
                t1 = dt
            new_x = self.data.x + self.data.dx * self.data.speed * t1
            new_y = self.data.y + self.data.dy * self.data.speed * t1

            self.hit_oid = -1
            for oid in boxes:
                if boxes[oid] != self and boxes[oid].is_alive():
                    if self.collide(new_x, new_y, boxes[oid]):
                        self.hit_oid = oid
                        break
            if self.hit_oid < 0:
                keep_x = new_x
                keep_y = new_y
                keep_t1 = t1
            else:
                break
            t1 += tstep
        return keep_x, keep_y, keep_t1

    def move_binary_search(self, boxes, dt, min_size):
        original_x = self.data.x
        original_y = self.data.y
        while min_size >= 0.25 and dt > EPSILON:
            total_dx = self.data.dx * self.data.speed * dt
            total_dy = self.data.dy * self.data.speed * dt
            largest_delta = max(abs(total_dx), abs(total_dy))
            pixel_step = min_size
            if largest_delta > pixel_step:
                tstep = pixel_step * dt / largest_delta
            else:
                tstep = dt
            t1 = tstep
            keep_x, keep_y, t1 = self.move_until_hit_or_time(boxes, tstep, dt, t1)
                
            if abs(keep_x - self.data.x) > EPSILON or abs(keep_y - self.data.y) > EPSILON:
                self.data.changed = True
            self.data.x = keep_x
            self.data.y = keep_y
            dt -= t1
            min_size /= 2.0
        # use manhattan distance to avoid sqrt
        distance = abs(original_x - self.data.x) + abs(original_y - self.data.y)
        self.add_distance(distance)
        return

    # boxes is a dictionary of oid -> objects
    # dt is the amount of time since last evolve
    # min_size is smallest dimension of any object
    # self.hit_oid > 0 if collision stopped motion at smallest scale
    def evolve(self, engine, boxes, dt, min_size):
        """
        Move objects by minimum size increments, until collision occurs.
        Then, do binary search to find point of collision.
        """
        # if object is moving
        self.hit_oid = -1
        if abs(self.data.speed) > EPSILON and (abs(self.data.dx) > 0. or abs(self.data.dy) > 0.) and self.data.is_alive():
            self.move_binary_search(boxes, dt, min_size)
        if self.data.is_dying():
            self.add_dying_percent(dt)
        return

    # collision related methods
    def get_x(self):
        return self.data.x
    def get_y(self):
        return self.data.y
    def get_center(self):
        xc = self.data.x + self.data.w/2.
        yc = self.data.y + self.data.h/2.
        return (xc, yc)
    def get_edge_point(self, dx, dy, w, h):
        """
        Find just outside the circumference point that is in dx,dy from center
        Adjust for w(idth) and h(eight) of object to be placed there.
        """
        (xc, yc) = self.get_center()
        if abs(dx) > abs(dy):
            if dx > 0.:
                x = self.data.x + self.data.w + w
            else:
                x = self.data.x - w
                x -= w
            t = (x - xc)/dx
            y = yc + dy*t
        else:
            if dy > 0.:
                y = self.data.y + self.data.h + h
            else:
                y = self.data.y - h
                y -= h
            t = (y - yc)/dy
            x = xc + dx*t
        return (x-w/2., y-h/2.)
    def get_box(self):
        return (self.data.x, self.data.y, self.data.w, self.data.h)

    def contains(self, nx, ny, hx, hy, hw, hh):
        """Returns True if needle is in haystack"""
        
        return (nx >= hx and nx <= hx + hw and
                ny >= hy and ny <= hy + hh)
        
    def collide(self, x2, y2, other):
        (x1, y1, w1, h1) = other.get_box()
        (oldx, oldy, w2, h2) = self.get_box()
        return (self.contains(x1,      y1,       x2,y2,w2,h2) or
                self.contains(x1,      y1 + h1,  x2,y2,w2,h2) or
                self.contains(x1 + w1, y1,       x2,y2,w2,h2) or
                self.contains(x1 + w1, y1 + h1,  x2,y2,w2,h2) or
                self.contains(x2,      y2,       x1,y1,w1,h1) or
                self.contains(x2,      y2 + h2,  x1,y1,w1,h1) or
                self.contains(x2 + w2, y2,       x1,y1,w1,h1) or
                self.contains(x2 + w2, y2 + h2,  x1,y1,w1,h1))
        

    # velocity and movement related methods
    def direction_unit_vector(self):
        return (self.data.dx, self.data.dy)
        
    def set_direction_degrees(self, degrees):
        r = math.radians(degrees)
        new_dy = math.sin(r)
        new_dx = math.cos(r)
        if abs(new_dx - self.data.dx) > 0.001 or abs(new_dy - self.data.dy) > 0.001:
            self.data.changed = True
        self.data.dx = new_dx
        self.data.dy = new_dy
        return
        
    def set_direction(self, new_dx, new_dy):
        if abs(new_dx - self.data.dx) > 0.001 or abs(new_dy - self.data.dy) > 0.001:
            self.data.changed = True
        self.data.dx = new_dx
        self.data.dy = new_dy
        return
        
    def add_distance(self, new_distance):
        self.data.add_distance(new_distance)
        self.data.changed = True
        return

    def get_speed(self):
        return self.data.speed
        
    def set_speed(self, new_speed):
        if abs(new_speed - self.data.speed) > EPSILON:
            self.data.changed = True
        self.data.speed = new_speed
        return

    def is_alive(self):
        return self.data.is_alive()
    def is_dying(self):
        return self.data.is_dying()
    def is_dead(self):
        return self.data.is_dead()
    def set_alive(self):
        self.data.set_alive()
        self.data.changed = True
        return
    def set_dying(self):
        self.data.set_dying()
        self.data.set_dying_percent(0.)
        self.data.changed = True
        return
    def set_dead(self):
        self.data.set_dead()
        self.data.changed = True
        return
    def add_dying_percent(self, dt):
        dp = self.data.get_dying_percent() + dt/DYING_TIME
        self.data.set_dying_percent(dp)
        if dp >= 1.0:
            self.set_dead()
        self.data.changed = True
        return

        
    # display related methods
    def position_str(self):
        return "(%f,%f)" % (self.data.x, self.data.y)
        
    def __str__(self):
        return str(self.data)
        
    def __repr__(self):
        return str(self)

        
