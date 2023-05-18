import "dart:convert";

import "errors.dart";
import "players.dart";
import "state.dart";
import "../session.dart";
import "../utils.dart";

typedef ErrorHandler = void Function(TicTacToeException error);

final _roomsCache = <String, Room>{};

class Room {
  final String id;
  List<String> logs;
  Pair<Player, Player?> players;
  final state = GameState();

  bool get started => state.started;
  bool get ended => state.ended;

  final ClientSession _http;

  WebSocketBroadcastChannel? _communicateWebSocket;
  WebSocketBroadcastChannel get communicateWebSocket => _communicateWebSocket ??= WebSocketBroadcastChannel.connect(
        websocketUri(
          "/tic-tac-toe/room/$id",
          {"id": _http.clientUser?.id.toString() ?? ""},
        ),
      );

  Stream<Room>? _updateStream;
  Stream<Room> get updateStream => _updateStream ??= _pollChanges().asBroadcastStream();

  Set<ErrorHandler> errorHandlers = <ErrorHandler>{};

  Room(
    Map<String, dynamic> data, {
    WebSocketBroadcastChannel? websocket,
    required ClientSession session,
  })  : id = data["id"],
        logs = List<String>.from(data["logs"]),
        players = Player.pairFromJson(data["players"]),
        _communicateWebSocket = websocket,
        _http = session {
    if (data["state"] != null) state.update(data["state"]);
  }

  void update(Map<String, dynamic> data) {
    assert(id == data["id"]);
    logs = List<String>.from(data["logs"]);
    players = Player.pairFromJson(data["players"]);
    if (data["state"] != null) state.update(data["state"]);
  }

  static Future<Room> fromId({required String id, required ClientSession session}) async {
    var cached = _roomsCache[id];
    if (cached != null && cached.communicateWebSocket.closeCode == null) return cached;

    var websocket = WebSocketBroadcastChannel.connect(
      websocketUri(
        "/tic-tac-toe/room/$id",
        {"id": session.clientUser?.id.toString() ?? ""},
      ),
    );
    var data = jsonDecode(await websocket.stream.first);
    if (data["error"]) throw TicTacToeException(data["message"]);

    return _roomsCache[id] = Room(data["data"], websocket: websocket, session: session);
  }

  static Future<Room> create({required ClientSession session}) async {
    var websocket = WebSocketBroadcastChannel.connect(
      websocketUri(
        "/tic-tac-toe/create",
        {"id": session.clientUser?.id.toString() ?? ""},
      ),
    );
    var data = jsonDecode(await websocket.stream.first);
    if (data["error"]) throw TicTacToeException(data["message"]);

    var room = Room(data["data"], websocket: websocket, session: session);
    return _roomsCache[room.id] = room;
  }

  Stream<Room> _pollChanges() async* {
    addErrorHandler((error) => error.showMessage());
    await for (var message in communicateWebSocket.stream) {
      var data = jsonDecode(message);
      if (data["error"]) {
        for (var handler in errorHandlers) {
          handler(TicTacToeException(data["message"]));
        }
      } else {
        update(data["data"]);
        yield this;
      }
    }
  }

  void addErrorHandler(ErrorHandler handler) {
    errorHandlers.add(handler);
  }

  void removeErrorHandler(ErrorHandler handler) {
    errorHandlers.remove(handler);
  }

  void sendString(String data) => communicateWebSocket.sink.add(data);
  void move(int row, int column) => sendString("MOVE $row $column");
  void start() => sendString("START");
  void chat(String content) => sendString("CHAT $content");
}

class RoomsLoader {
  final ClientSession _http;

  RoomsLoader({required ClientSession session}) : _http = session;

  Stream<List<Room>>? _roomsFetcher;
  Stream<List<Room>> get roomsFetcher => _roomsFetcher ??= fetchRooms().asBroadcastStream();

  Stream<List<Room>> fetchRooms() async* {
    var websocket = WebSocketBroadcastChannel.connect(websocketUri("/tic-tac-toe/rooms"));
    await for (var message in websocket.stream) {
      var data = List<Map<String, dynamic>>.from(jsonDecode(message));
      yield List<Room>.generate(data.length, (index) => Room(data[index], session: _http));
    }
  }

  void resetRoomsFetcher() => _roomsFetcher = null;
}
