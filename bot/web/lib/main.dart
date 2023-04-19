import "package:flutter/material.dart";

import "core/session.dart";
import "pages/main.dart";

void main() {
  var session = ClientSession.create();

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
