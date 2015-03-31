#!/usr/bin/env python
import sys
sys.path.append("..")
from game_engine import GameEngine

def main():
    g = GameEngine()
    oid1 = g.get_player1_oid()
    oid2 = g.get_player2_oid()
    g.set_player_speed_slow(oid1)
    g.set_player_direction(oid1, -45)
    g.set_player_speed_fast(oid2)
    g.set_player_direction(oid2, 180)
    print g, "\n"
    for i in range(3):
        g.evolve(.1)
        print g
        print g.get_changed_objects(), "\n"
        g.clear_changed_objects()
    return

main()
