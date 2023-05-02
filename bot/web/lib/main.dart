import "package:flutter/material.dart";

import "src/session.dart";
import "pages/main.dart";

Future<void> main() async {
  var session = await ClientSession.create();

  runApp(MainApp(session: session));
}

class MainApp extends StatelessWidget {
  final ClientSession _http;

  const MainApp({super.key, required ClientSession session}) : _http = session;

  @override
  Widget build(BuildContext context) {
    var routes = {"/": (context) => MainPage(session: _http)};

    return MaterialApp(
      title: "Haruka",
      theme: ThemeData.dark(),
      initialRoute: "/",
      routes: routes,
    );
  }
}
