const BOARD_SIZE = 15;

class GameState {
  final board = List<List<int?>>.generate(
    BOARD_SIZE,
    (index) => List<int?>.generate(
      BOARD_SIZE,
      (index) => null,
      growable: false,
    ),
    growable: false,
  );
  bool started = false;
  bool ended = false;
  int turn = 0;
  int? winner;

  GameState([Map<String, dynamic>? data]) {
    if (data != null) {
      update(data);
    }
  }

  void update(Map<String, dynamic> data) {
    for (int i = 0; i < BOARD_SIZE; i++) {
      for (int j = 0; j < BOARD_SIZE; j++) {
        board[i][j] = data["board"][i][j];
      }
    }

    started = data["started"];
    ended = data["ended"];
    turn = data["turn"];
    winner = data["winner"];
  }
}
