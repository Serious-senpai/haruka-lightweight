import "package:flutter/material.dart";

import "template.dart";
import "../src/environment.dart";
import "../src/session.dart";
import "../src/utils.dart";
import "../src/tic_tac_toe/errors.dart";
import "../src/tic_tac_toe/rooms.dart";
import "../src/tic_tac_toe/state.dart";

final _chatController = TextEditingController();

class TicTacToePage extends StatefulWidget {
  final ClientSession _http;
  final String? roomId;

  const TicTacToePage({Key? key, this.roomId, required ClientSession session})
      : _http = session,
        super(key: key);

  @override
  State<TicTacToePage> createState() => _TicTacToePageState();
}

class _TicTacToePageState extends State<TicTacToePage> {
  ClientSession get _http => widget._http;

  Size get screenSize => MediaQuery.of(context).size;

  void refresh() => setState(() {});

  @override
  Widget build(BuildContext context) {
    var roomId = widget.roomId;

    if (roomId == null) {
      _http.roomsLoader.request();
      return TemplateScaffold(
        session: _http,
        title: "Tic-Tac-Toe game",
        child: StreamBuilder(
          stream: _http.roomsLoader.roomsFetcher,
          builder: (context, snapshot) {
            var error = snapshot.error;
            if (error != null) throw error;

            var data = snapshot.data;
            if (data == null) return Center(child: loadingIndicator());

            return ListView.builder(
              padding: const EdgeInsets.all(10.0),
              itemCount: data.length + 1,
              itemBuilder: (context, index) {
                if (index == 0) {
                  return Row(
                    children: [
                      IconButton(
                        onPressed: () {
                          _http.roomsLoader.resetRoomsFetcher();
                          refresh();
                        },
                        icon: const Icon(Icons.refresh_outlined),
                      ),
                      TextButton(
                        onPressed: () async {
                          try {
                            var room = await Room.create(session: _http);
                            refresh();
                            if (mounted) navigate(context: context, routeName: "/tic-tac-toe/room/${room.id}");
                          } on TicTacToeException catch (e) {
                            await e.showMessage();
                          }
                        },
                        child: const Text("Host a new game"),
                      ),
                    ],
                  );
                }

                var room = data[index - 1];
                return ListTile(
                  title: Text(room.players.second == null ? "${room.players.first.user.displayName} vs --" : "${room.players.first.user.displayName} vs ${room.players.second!.user.displayName}"),
                  subtitle: Text(room.started ? "Started" : "Not started"),
                  onTap: () => navigate(context: context, routeName: "/tic-tac-toe/room/${room.id}"),
                );
              },
            );
          },
        ),
      );
    }

    return TemplateScaffold(
      session: _http,
      title: "Tic-Tac-Toe room $roomId",
      child: FutureBuilder(
        future: Room.fromId(id: widget.roomId!, session: _http),
        builder: (context, snapshot) {
          var error = snapshot.error;
          if (error != null) {
            if (error is TicTacToeException) error.showMessage();
            throw error;
          }

          var data = snapshot.data;
          if (data == null) return Center(child: loadingIndicator());

          return StreamBuilder(
            initialData: data,
            stream: data.updateStream,
            builder: (context, snapshot) {
              var data = snapshot.data!;
              var winner = data.state.winner == 0
                  ? data.players.first
                  : data.state.winner == 1
                      ? data.players.second
                      : null;

              var chatFocus = FocusNode();
              return SingleChildScrollView(
                scrollDirection: Axis.vertical,
                child: SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.start,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Column(
                        mainAxisAlignment: MainAxisAlignment.start,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              data.players.first.user.displayAvatar(),
                              seperator,
                              Text(data.players.first.user.displayName, style: TextStyle(color: data.state.turn == 0 ? themeColor : null)),
                              seperator,
                              (winner != null && winner == data.players.first) ? const Icon(Icons.emoji_events_outlined, color: Colors.yellow) : const SizedBox.shrink(),
                            ],
                          ),
                          seperator,
                          data.players.second == null
                              ? const Text("Waiting for another player...")
                              : Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    data.players.second!.user.displayAvatar(),
                                    seperator,
                                    Text(data.players.second!.user.displayName, style: TextStyle(color: data.state.turn == 1 ? themeColor : null)),
                                    seperator,
                                    (winner != null && winner == data.players.second) ? const Icon(Icons.emoji_events_outlined, color: Colors.yellow) : const SizedBox.shrink(),
                                  ],
                                ),
                          seperator,
                          Padding(
                            padding: const EdgeInsets.all(8.0),
                            child: Column(
                              children: List<Widget>.generate(
                                BOARD_SIZE,
                                (row) => Row(
                                  children: List<Widget>.generate(
                                    BOARD_SIZE,
                                    (column) => GestureDetector(
                                      onTap: () => data.move(row, column),
                                      child: Container(
                                        decoration: BoxDecoration(border: Border.all(color: Colors.white)),
                                        padding: const EdgeInsets.all(3.0),
                                        width: 40.0,
                                        height: 40.0,
                                        child: data.state.board[row][column] == null ? const SizedBox.shrink() : Icon(data.state.board[row][column] == 0 ? Icons.close : Icons.circle_outlined),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                          seperator,
                          data.started ? Text(data.ended ? "Game ended" : "Game started") : TextButton(onPressed: data.start, child: const Text("START")),
                        ],
                      ),
                      Column(
                        mainAxisAlignment: MainAxisAlignment.start,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            decoration: BoxDecoration(border: Border.all(color: Colors.white)),
                            width: 400.0,
                            child: TextField(
                              controller: _chatController,
                              focusNode: chatFocus,
                              decoration: const InputDecoration(
                                hintText: "Chat input",
                                hintStyle: TextStyle(color: Colors.grey, fontStyle: FontStyle.italic),
                              ),
                              showCursor: true,
                              autofocus: true,
                              autocorrect: false,
                              enableSuggestions: false,
                              onSubmitted: (value) {
                                _chatController.clear();
                                chatFocus.requestFocus();
                                data.chat(value);
                              },
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.all(3.0),
                            decoration: BoxDecoration(border: Border.all(color: Colors.white)),
                            width: 400.0,
                            height: screenSize.height * 2 / 3,
                            child: SingleChildScrollView(child: Text(data.logs.reversed.join("\n"), overflow: TextOverflow.visible)),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
