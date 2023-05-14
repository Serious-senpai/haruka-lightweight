import "../users.dart";
import "../utils.dart";

class Player {
  final User user;

  Player(Map<String, dynamic> data) : user = User(data["user"]);

  static Pair<Player, Player?> pairFromJson(List<Map<String, dynamic>?> data) => Pair<Player, Player?>(
        Player(data[0]!),
        data[1] == null ? null : Player(data[1]!),
      );
}
