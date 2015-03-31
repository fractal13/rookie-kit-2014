#!/usr/bin/env python
import sqlite3 as sqlite
import os, sys, getopt

TS_NONE = 0
TS_PREGAME = 1
TS_STARTED = 2
TS_OVER = 3

TOURNAMENT_NONE = 0
TOURNAMENT_NOT_AVAILABLE = 100
TOURNAMENT_AVAILABLE = 101
TOURNAMENT_STARTED = 102
TOURNAMENT_OVER = 103

class Tournament:

    def __init__(self):
        self.filename = "tournament.db"
        self.connection  = None
        self.cursor = None
        return

    def get_max_losses(self):
        var = "max_losses"
        max_losses = 0
        val = self.get_data(var)
        if val is not None:
            max_losses = int(val)
        return max_losses
        
    def set_max_losses(self, ml):
        var = "max_losses"
        val = self.add_data(var, str(ml))
        return

    def get_tournament_state(self):
        var = "tournament_state"
        state = TOURNAMENT_NOT_AVAILABLE
        val = self.get_data(var)
        if val is not None:
            state = int(val)
        return state

    def set_tournament_state(self, state):
        var = "tournament_state"
        val = self.add_data(var, str(state))
        return

    def open(self):
        exists = os.path.exists(self.filename)
        self.connection = sqlite.connect(self.filename)
        self.cursor = self.connection.cursor()
        if not exists:
            self.create_tables()
        return

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection  = None
            self.cursor = None
        return

    def create_tables(self):
        if self.cursor:
            self.cursor.execute("""CREATE TABLE players
                                   (name)""")
            self.cursor.execute("""CREATE TABLE games
                                   (player1, player2, state, winner)""")
            self.cursor.execute("""CREATE TABLE data
                                   (var, value)""")
            self.connection.commit()
        return

    def data_exists(self, var):
        if self.cursor:
            self.cursor.execute("""SELECT value FROM data WHERE var = ?""", (str(var),))
            row = self.cursor.fetchone()
            if row is not None:
                return True
        return False
        
    def add_data(self, var, val):
        if  self.cursor:
            if not self.data_exists(var):
                self.cursor.execute("""INSERT INTO data
                                       (var, value) 
                                       VALUES (?,?)""",
                                    (str(var), str(val)))
            else:
                self.cursor.execute("""UPDATE data SET value = ? WHERE var = ?""", (str(val), str(var)))
            self.connection.commit()
        return
        
    def get_data(self, var):
        if  self.cursor:
            self.cursor.execute("""SELECT value FROM data WHERE var = ?""", (str(var),))
            row = self.cursor.fetchone()
            if row is not None:
                val = str(row[0])
                return val
        return None

    def player_exists(self, name):
        if self.cursor:
            self.cursor.execute("""SELECT name FROM players WHERE name = ?""", (name,))
            row = self.cursor.fetchone()
            if row is not None:
                return True
        
        return False
        
    def add_player(self, name):
        if  self.cursor and not self.player_exists(name):
            self.cursor.execute("""INSERT INTO players
                                   (name) 
                                   VALUES (?)""",
                                (name,))
            self.connection.commit()
        return
        
    def delete_player(self, name):
        if self.cursor and self.player_exists(name):
            self.cursor.execute("""DELETE FROM players WHERE name = ?""",
                                (str(name), ))
            self.connection.commit()
        return
        
    def list_players(self):
        players = []
        if self.cursor:
            self.cursor.execute("""SELECT name FROM players""", ())
            done = False
            while not done:
                row = self.cursor.fetchone()
                if row is None:
                    done = True
                else:
                    players.append(str(row[0]))
        return players

    def list_games(self):
        games = []
        if self.cursor:
            self.cursor.execute("""SELECT player1, player2, state, winner FROM games""", ())
            done = False
            while not done:
                row = self.cursor.fetchone()
                if row is None:
                    done = True
                else:
                    games.append( (str(row[0]),str(row[1]),str(row[2]),str(row[3])) )
        return games

    def list_games_in_state(self, state):
        games = []
        if self.cursor:
            self.cursor.execute("""SELECT player1, player2, state, winner FROM games WHERE state = ?""", (str(state),))
            done = False
            while not done:
                row = self.cursor.fetchone()
                if row is None:
                    done = True
                else:
                    games.append( (str(row[0]),str(row[1]),str(row[2]),str(row[3])) )
        return games

    def game_exists(self, p1, p2):
        if self.cursor:
            self.cursor.execute("""SELECT state FROM games WHERE player1 = ? AND player2 = ?""", (str(p1), str(p2)))
            row = self.cursor.fetchone()
            if row is not None:
                return True
        return False
        
    def either_game_exists(self, p1, p2):
        return self.game_exists(p1, p2) or self.game_exists(p2, p1)
        
    def add_game(self, p1, p2):
        if  self.cursor and (not self.either_game_exists(p1, p2)):
            self.add_player(p1)
            self.add_player(p2)
            self.cursor.execute("""INSERT INTO games
                                   (player1, player2, state, winner) 
                                   VALUES (?,?,?,?)""",
                                (str(p1), str(p2), str(TS_PREGAME), ""))
            self.connection.commit()
        return
        
    def start_game(self, p1, p2):
        if not self.either_game_exists(p1, p2):
            self.add_game(p1, p2)
        if self.cursor and self.game_exists(p1, p2):
            self.cursor.execute("""UPDATE games SET state = ? WHERE player1 = ? AND player2 = ?""",
                                (str(TS_STARTED), str(p1), str(p2)))
            self.connection.commit()
        elif self.cursor and self.game_exists(p2, p1):
            self.cursor.execute("""UPDATE games SET state = ? WHERE player1 = ? AND player2 = ?""",
                                (str(TS_STARTED), str(p2), str(p1)))
            self.connection.commit()
        return
        
    def end_game(self, p1, p2, winner):
        if not self.either_game_exists(p1, p2):
            self.add_game(p1, p2)
        if self.cursor and self.game_exists(p1, p2):
            self.cursor.execute("""UPDATE games SET state = ?, winner = ? WHERE player1 = ? AND player2 = ?""",
                                (str(TS_OVER), str(winner), str(p1), str(p2)))
            self.connection.commit()
        elif self.cursor and self.game_exists(p2, p1):
            self.cursor.execute("""UPDATE games SET state = ?, winner = ? WHERE player1 = ? AND player2 = ?""",
                                (str(TS_OVER), str(winner), str(p2), str(p1)))
            self.connection.commit()
        return
        
    def delete_game(self, p1, p2):
        if self.cursor and self.game_exists(p1, p2):
            self.cursor.execute("""DELETE FROM games WHERE player1 = ? AND player2 = ?""",
                                (str(p1), str(p2)))
            self.connection.commit()
        elif self.cursor and self.game_exists(p2, p1):
            self.cursor.execute("""DELETE FROM games WHERE player1 = ? AND player2 = ?""",
                                (str(p2), str(p1)))
            self.connection.commit()
        return
        
    def get_game(self, p1, p2):
        if self.cursor and self.game_exists(p1, p2):
            self.cursor.execute("""SELECT state, winner FROM games WHERE player1 = ? AND player2 = ?""", (str(p1), str(p2)))
            row = self.cursor.fetchone()
            if row is not None:
                return (int(row[0]), str(row[1]))
        elif self.cursor and self.game_exists(p2, p1):
            self.cursor.execute("""SELECT state, winner FROM games WHERE player1 = ? AND player2 = ?""", (str(p2), str(p1)))
            row = self.cursor.fetchone()
            if row is not None:
                return (int(row[0]), str(row[1]))
        return (TS_NONE, "")


    def count_losses(self, player):
        count = 1000
        if self.cursor:
            count = 0
            self.cursor.execute("""SELECT state, winner FROM games WHERE (player1 = ? OR player2 = ?) AND state = ? AND winner != ?""",
                                (str(player), str(player), str(TS_OVER), str(player)))
            for row in self.cursor.fetchall():
                count += 1
        return count
        
    def count_wins(self, player):
        count = 0
        if self.cursor:
            self.cursor.execute("""SELECT state, winner FROM games WHERE (player1 = ? OR player2 = ?) AND state = ? AND winner == ?""",
                                (str(player), str(player), str(TS_OVER), str(player)))
            for row in self.cursor.fetchall():
                count += 1
        return count
        
    def player_in_game(self, player):
        if self.cursor:
            count = 0
            self.cursor.execute("""SELECT state FROM games WHERE (player1 = ? OR player2 = ?) AND (state = ? OR state = ?)""",
                                (str(player), str(player), str(TS_PREGAME), str(TS_STARTED)))
            for row in self.cursor.fetchall():
                count += 1
        return count

        
    def get_in_game_players(self):
        players = []
        all_players = self.list_players()
        for p in all_players:
            if self.player_in_game(p):
                players.append(p)
        return players
        
    def get_not_in_game_players(self):
        players = []
        all_players = self.list_players()
        for p in all_players:
            if not self.player_in_game(p):
                players.append(p)
        return players
        
    def get_eligible_players(self):
        """max_losses or in_game makes ineligible"""
        max_losses = self.get_max_losses()
        players = []
        all_players = self.list_players()
        for p in all_players:
            losses = self.count_losses(p)
            if losses < max_losses and not self.player_in_game(p):
                players.append(p)
        return players
        
    def get_ineligible_players(self):
        """max_losses or in_game makes ineligible"""
        max_losses = self.get_max_losses()
        players = []
        all_players = self.list_players()
        for p in all_players:
            losses = self.count_losses(p)
            if losses >= max_losses or self.player_in_game(p):
                players.append(p)
        return players

    def reset(self):
        for g in self.list_games():
            self.delete_game(g[0], g[1])
        for p in self.list_players():
            self.delete_player(p)
        return
        
    def get_player_stats(self):
        """list of (name, wins, losses) tuples"""
        stats = []
        all_players = self.list_players()
        for p in all_players:
            losses = self.count_losses(p)
            wins = self.count_wins(p)
            stats.append( (p, wins, losses) )
        return stats
        


def usage():
    print "usage: %s options" % (sys.argv[0])
    print "options:"
    print "-h|--help                 : show this message and exit"
    print "-e|--eligible             : list eligible players"
    print "-i|--ineligible           : list ineligible players"
    print "-p|--players              : list all players"
    print "-g|--in-game              : list all players in running game"
    print "-G|--not-in-game          : list all players not in running game"
    print "-l|--games                : list all games"
    print "-L|--games-in-state state : list all games in state (%d=NONE, %d=PRE, %d=STARTED, %d=OVER)" % \
        (TS_NONE, TS_PREGAME, TS_STARTED, TS_OVER)
    print "-m|--max-losses           : show max losses"
    print "-M|--set-max-losses value : set max losses"
    print "-s|--state                : show tournament state"
    print "-S|--set-state value      : set tournament state (%d=NA, %d=AVAIL, %d=STARTED, %d=OVER)" % \
        (TOURNAMENT_NOT_AVAILABLE, TOURNAMENT_AVAILABLE, TOURNAMENT_STARTED, TOURNAMENT_OVER)
    print "-d|--delete-game          : delete a game (player1, player2 required)"
    print "-E|--end-game             : end a game (player1, player2, winner required)"
    print "-1|--player1 value        : player 1"
    print "-2|--player2 value        : player 2"
    print "-w|--winner value         : winner"
    print "-R|--reset                : ERASE THE DATABASE and start over (both required)"
    print "-r|--really-reset         : REALLY ERASE THE DATABASE and start over (both required)"
    print "-a|--all-stats            : print stats for all players"
    return

def main():
    try:
        short_opts = "heipgGlL:mM:sS:dE1:2:w:Rra"
        long_opts = ["help", "eligible", "ineligible", "players", "in-game", "not-in-game",
                     "games", "games-in-state", "max-losses", "set-max-losses",
                     "state", "set-state", "delete-game", "end-game",
                     "player1", "player2", "winner",
                     "reset", "really-reset", "all-stats"]
        opts, args = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as e:
        print str(e)
        usage()
        sys.exit(1)

    show_help = False
    list_eligible = False
    list_ineligible = False
    list_players = False
    list_in_game_players = False
    list_not_in_game_players = False
    list_games = False
    list_games_in_state = False
    game_state = TS_NONE
    list_max_losses = False
    set_max_losses = False
    max_losses = 0
    list_state = False
    set_state = False
    tournament_state = TOURNAMENT_NONE
    delete_game = False
    end_game = False
    player1 = None
    player2 = None
    winner = None
    reset = False
    really_reset = False
    list_all_stats = False
    for o, a in opts:
        if o in ("-h", "--help"):
            show_help = True
        elif o in ("-e", "--eligible"):
            list_eligible = True
        elif o in ("-i", "--ineligible"):
            list_ineligible = True
        elif o in ("-p", "--players"):
            list_players = True
        elif o in ("-g", "--in-game"):
            list_in_game_players = True
        elif o in ("-G", "--not-in-game"):
            list_not_in_game_players = True
        elif o in ("-l", "--games"):
            list_games = True
        elif o in ("-L", "--games-in-state"):
            list_games_in_state = True
            game_state = a
        elif o in ("-m", "--max-losses"):
            list_max_losses = True
        elif o in ("-M", "--set-max-losses"):
            set_max_losses = True
            max_losses = int(a)
        elif o in ("-s", "--state"):
            list_state = True
        elif o in ("-S", "--set-state"):
            set_state = True
            tournament_state = int(a)
        elif o in ("-d", "--delete-game"):
            delete_game = True
        elif o in ("-E", "--end-game"):
            end_game = True
        elif o in ("-1", "--player1"):
            player1 = a
        elif o in ("-2", "--player2"):
            player2 = a
        elif o in ("-w", "--winner"):
            winner = a
        elif o in ("-R", "--reset"):
            reset = True
        elif o in ("-r", "--really-reset"):
            really_reset = True
        elif o in ("-a", "--all-stats"):
            list_all_stats = True
        else:
            print "Unexpected option: %s" % (o)
            usage()
            sys.exit(1)
    if show_help:
        usage()
        sys.exit(1)

    t = Tournament()
    t.open()
    if list_eligible:
        print "Eligible: '%s'" % ("';'".join(t.get_eligible_players()),)
        print
    if list_ineligible:
        print "Ineligible: '%s'" % ("';'".join(t.get_ineligible_players()),)
        print
    if list_players:
        print "Players: '%s'" % ("';'".join(t.list_players()),)
        print
    if list_in_game_players:
        print "InGamePlayers: '%s'" % ("';'".join(t.get_in_game_players()),)
        print
    if list_not_in_game_players:
        print "NotInGamePlayers: '%s'" % ("';'".join(t.get_not_in_game_players()),)
        print
    if list_games:
        print "Games: '%s'" % ("';'".join([ str(x) for x in t.list_games() ]),)
        print
    if delete_game:
        if player1 and player2:
            print "Delete: '%s' vs '%s'" % (player1, player2)
            t.delete_game(player1, player2)
        else:
            print "Delete game must specify both players."
        print
    if end_game:
        if player1 and player2 and winner:
            print "EndGame: '%s' vs '%s' => '%s'" % (player1, player2, winner)
            t.end_game(player1, player2, winner)
        else:
            print "End game must specify both players and the winner."
        print
    if list_games_in_state:
        print "Games in %s: '%s'" % (game_state, "';'".join([ str(x) for x in t.list_games_in_state(game_state) ]),)
        print
    if set_max_losses:
        print "SetMaxLosses: '%d'" % (max_losses,)
        t.set_max_losses(max_losses)
        print
    if list_max_losses:
        print "MaxLosses: '%d'" % (t.get_max_losses(),)
        print
    if set_state:
        print "SetState: '%d'" % (tournament_state,)
        t.set_tournament_state(tournament_state)
        print
    if list_state:
        print "State: '%d'" % (t.get_tournament_state(),)
        print
    if reset and not really_reset:
        print "Both resets are required."
        print
    if not reset and really_reset:
        print "Both resets are required."
        print
    if reset and really_reset:
        print "Resetting the database."
        t.reset()
        print
    if list_all_stats:
        print "Stats (name, wins, losses):"
        stats = t.get_player_stats()
        
        for s in sorted(sorted(stats, key=lambda s: -s[2]), key=lambda s: -s[1]):
            print s
        print

    t.close()
    sys.exit(0)
    return
    
if __name__ == "__main__":
    main()


        

        
