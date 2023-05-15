import re

from ...tic_tac_toe import BOARD_SIZE


valid_index_group = "|".join(str(i) for i in range(BOARD_SIZE))
MOVE = re.compile(rf"^MOVE ({valid_index_group}) ({valid_index_group})$")
START = re.compile(r"^START$")
