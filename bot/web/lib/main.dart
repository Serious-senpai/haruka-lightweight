import "package:flutter/material.dart";
import "package:http/http.dart";

import "customs.dart";
import "pages/main.dart";

void main() {
  print("Release mode: $release");
  var client = Client();

  runApp(MainApp(client: client));
}

class MainApp extends StatelessWidget {
  final Client _http;

  const MainApp({super.key, required Client client}) : _http = client;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "Haruka",
      theme: ThemeData.dark(),
      initialRoute: "/",
      routes: {
        "/": (context) => MainPage(client: _http),
      },
    );
  }
}
