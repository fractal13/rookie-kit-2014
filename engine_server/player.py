import math
from common.player import PlayerData
from object import Object
from config import *
class Player(Object):
    
    def __init__(self, x, y, w, h):
        # don't call base class constructor, because
        # data is initialized here
        self.data = PlayerData(x, y, w, h)
        self.data.set_health(HEALTH_PLAYER)
        self.data.set_max_health(HEALTH_PLAYER)
        self.set_missile_direction_degrees(0.0)
        self.set_missile_mana(0.0)
        self.set_missile_mana_recharge_rate()
        self.set_missile_mana_max()
        self.set_move_mana(0.0)
        self.set_move_mana_recharge_rate()
        self.set_move_mana_max()
        self.assign_object_id()
        self.hit_oid = -1   # the oid of the object we hit
        self.has_quit = False # has the player given up (or disconncected)
        return

    def set_quit(self):
        self.has_quit = True
        return
    def get_quit(self):
        return self.has_quit
        
    def set_speed(self, (speed, min_xp)):
        if self.data.experience < min_xp:
            return
        Object.set_speed(self, speed)
        return

    def set_missile_range(self, (mrange, min_xp)):
        if self.data.experience < min_xp:
            return
        if abs(mrange - self.data.missile_range) > EPSILON:
            self.data.changed = True
        self.data.missile_range = mrange
        return
        
    def set_missile_direction_degrees(self, degrees):
        r = math.radians(degrees)
        new_dy = math.sin(r)
        new_dx = math.cos(r)
        if abs(new_dx - self.data.missile_dx) > EPSILON or abs(new_dy - self.data.missile_dy) > EPSILON:
            self.data.changed = True
        self.data.missile_dx = new_dx
        self.data.missile_dy = new_dy
        return

    def set_missile_power(self, (power, min_xp)):
        if self.data.experience < min_xp:
            return
        if abs(power - self.data.missile_power) > EPSILON:
            self.data.changed = True
        self.data.missile_power = power
        return
        
    def get_missile_dx(self):
        return self.data.missile_dx
    def get_missile_dy(self):
        return self.data.missile_dy
    def get_missile_range(self):
        return self.data.missile_range
    def get_missile_power(self):
        return self.data.missile_power
    def get_missile_mana(self):
        return self.data.missile_mana
    def get_missile_mana_recharge_rate(self):
        return self.data.missile_mana_recharge_rate
    def get_missile_mana_max(self):
        return self.data.missile_mana_max
    def set_missile_mana(self, value):
        self.data.set_missile_mana(value)
    def set_missile_mana_max(self):
        i = 0
        j = 0
        while i < len(MISSILE_MANA_MAX) and self.data.experience + EPSILON >= MISSILE_MANA_MAX[i][1]:
            j = i
            i += 1
        value = MISSILE_MANA_MAX[j][0]
        if abs(value - self.data.missile_mana_max) > EPSILON:
            self.data.set_missile_mana_max(value)
            self.data.changed = True
        return
    def set_missile_mana_recharge_rate(self):
        i = 0
        j = 0
        while i < len(MISSILE_MANA_RECHARGE_RATE) and self.data.experience + EPSILON >= MISSILE_MANA_RECHARGE_RATE[i][1]:
            j = i
            i += 1
        value = MISSILE_MANA_RECHARGE_RATE[j][0]
        if abs(value - self.data.missile_mana_recharge_rate) > EPSILON:
            self.data.set_missile_mana_recharge_rate(value)
            self.data.changed = True
        return
    def recharge_missile_mana(self, mana_amount):
        if self.data.missile_mana < self.data.missile_mana_max:
            self.data.missile_mana += mana_amount
            self.data.changed = True
            if self.data.missile_mana > self.data.missile_mana_max:
                self.data.missile_mana = self.data.missile_mana_max
        return
    def consume_missile_mana(self, mana_amount):
        if self.data.missile_mana < mana_amount - EPSILON:
            return False
        self.data.missile_mana -= mana_amount
        self.data.changed = True
        return True

    def get_move_mana(self):
        return self.data.move_mana
    def get_move_mana_max(self):
        return self.data.move_mana_max
    def get_move_mana_recharge_rate(self):
        return self.data.move_mana_recharge_rate
    def set_move_mana(self, value):
        self.data.set_move_mana(value)
    def set_move_mana_max(self):
        i = 0
        j = 0
        while i < len(MOVE_MANA_MAX) and self.data.experience + EPSILON >= MOVE_MANA_MAX[i][1]:
            j = i
            i += 1
        value = MOVE_MANA_MAX[j][0]
        if abs(value - self.data.move_mana_max) > EPSILON:
            self.data.set_move_mana_max(value)
            self.data.changed = True
        return
    def set_move_mana_recharge_rate(self):
        i = 0
        j = 0
        while i < len(MOVE_MANA_RECHARGE_RATE) and self.data.experience + EPSILON >= MOVE_MANA_RECHARGE_RATE[i][1]:
            j = i
            i += 1
        value = MOVE_MANA_RECHARGE_RATE[j][0]
        if abs(value - self.data.move_mana_recharge_rate) > EPSILON:
            self.data.set_move_mana_recharge_rate(value)
            self.data.changed = True
        return
    def recharge_move_mana(self, mana_amount):
        if self.data.move_mana < self.data.move_mana_max:
            self.data.move_mana += mana_amount
            self.data.changed = True
            if self.data.move_mana > self.data.move_mana_max:
                self.data.move_mana = self.data.move_mana_max
        return
    def consume_move_mana(self, mana_amount):
        if self.data.move_mana < mana_amount - EPSILON:
            return False
        self.data.move_mana -= mana_amount
        self.data.changed = True
        return True
        
    def add_experience(self, new_experience):
        self.data.add_experience(new_experience)
        self.set_missile_mana_max()
        self.set_move_mana_max()
        self.data.changed = True
        return

    def evolve(self, engine, boxes, dt, min_size):
        if self.get_speed() >= 1.0:
            move_mana_cost = MOVE_MANA_COST_RATE * dt * math.log(self.get_speed()/10.)
            if not self.consume_move_mana(move_mana_cost):
                self.set_speed(PLAYER_SPEED_STOP)
        else:
            self.set_speed(PLAYER_SPEED_STOP)
        Object.evolve(self, engine, boxes, dt, min_size)
        self.recharge_missile_mana(self.get_missile_mana_recharge_rate()*dt)
        self.recharge_move_mana(self.get_move_mana_recharge_rate()*dt)
        return
