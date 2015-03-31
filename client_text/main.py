#!/usr/bin/env python
import sys, logging
sys.path.append('..')
from game_client import GameClient
def main():
    logging.basicConfig(level=logging.INFO)
    #logging.basicConfig(level=logging.DEBUG)
    g = GameClient()
    g.run()
    return
                
if __name__ == "__main__":
    main()
