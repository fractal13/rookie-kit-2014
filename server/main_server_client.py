MS_STATE_CONNECTED = 1
MS_STATE_LOGGED_IN = 2
MS_STATE_WAIT_DUAL_GAME = 3
MS_STATE_WAIT_SINGLE_GAME = 4
MS_STATE_AI_PLAYER = 5
MS_STATE_WAIT_TOURNAMENT_GAME = 6
MS_STATE_VIEWER = 7

class MainServerClient:
    def __init__(self, connection, address):
        self.sock = connection
        self.address = address
        self.state = MS_STATE_CONNECTED
        self.name  = ""
        self.opponent_name = ""
        return
