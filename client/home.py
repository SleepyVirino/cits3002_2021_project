
class Home():
    def __init__(self, id,owner_id, border_width=5, border_height=5, hand_size=4, max_player=4):
        self.owner_id = owner_id
        self.border_width = border_width
        self.border_height = border_height
        self.hand_size = hand_size
        self.max_player = max_player
        self.id = id
        self.player_names = {}
        self.player_nums = {}
        self.player_list = []



