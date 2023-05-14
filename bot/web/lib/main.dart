import "package:flutter/material.dart";

import "src/session.dart";
import "pages/main.dart";
import "pages/tic_tac_toe.dart";

Future<void> main() async {
  var session = await ClientSession.create();

  runApp(MainApp(session: session));
}

class MainApp extends StatelessWidget {
  final ClientSession _http;

  const MainApp({super.key, required ClientSession session}) : _http = session;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "Haruka",
      theme: ThemeData.dark(),
      routes: {
        "/": (context) => MainPage(session: _http),
        "/tic-tac-toe": (context) => TicTacToePage(session: _http),
      },
      onGenerateRoute: (settings) {
        var name = settings.name;
        if (name != null) {
          var pattern = RegExp(r"^\/tic-tac-toe\/room\/(.+?)\/?$");
          var roomId = pattern.firstMatch(name)!.group(1);
          return MaterialPageRoute(builder: (context) => TicTacToePage(roomId: roomId, session: _http));
        }
      },
    );
  }
}
