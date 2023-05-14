class GameState {
  final board = <List<int?>>[
    [null, null, null],
    [null, null, null],
    [null, null, null],
  ];
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
    for (int i = 0; i < 3; i++) {
      for (int j = 0; j < 3; j++) {
        board[i][j] = data["board"][i][j];
      }
    }

    started = data["started"];
    ended = data["ended"];
    turn = data["turn"];
    winner = data["winner"];
  }
}
