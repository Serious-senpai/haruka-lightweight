import "dart:convert";

import "package:http/http.dart";
import "package:flutter/material.dart";
import "package:flutter_markdown/flutter_markdown.dart";
import "package:url_launcher/url_launcher.dart";

import "../customs.dart";
import "../utils.dart";

class Command {
  String name;
  List<String> aliases;
  String brief;
  String description;
  String usage;

  Command(Map<String, dynamic> data)
      : name = data["name"],
        aliases = List<String>.from(data["aliases"]),
        brief = data["brief"],
        description = data["description"],
        usage = data["usage"];

  Widget display() => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(name, style: const TextStyle(color: themeColor, fontSize: 24)),
          Row(
            children: [
              const Text("Syntax ", style: TextStyle(fontWeight: FontWeight.bold)),
              MarkdownBody(data: "```\n$usage\n```"),
            ],
          ),
          MarkdownBody(data: description),
        ],
      );
}

class CommandsLoader {
  final Client _http;
  Future<List<Command>>? _fetcher;

  Future<List<Command>> get fetcher => _fetcher ??= _fetchCommands();

  CommandsLoader({required Client client}) : _http = client;

  Future<List<Command>> _fetchCommands() async {
    List<Map<String, dynamic>> data;
    if (release) {
      var response = await _http.get(Uri.parse("/commands"));
      data = List<Map<String, dynamic>>.from(jsonDecode(response.body));
    } else {
      data = <Map<String, dynamic>>[];
      for (var i = 0; i < 100; i++) {
        data.add(
          {
            "name": "name$i",
            "aliases": ["alias_1", "alias_2", "alias_3"],
            "brief": "category.name$i",
            "description": "description$i",
            "usage": "\$name$i <param>",
          },
        );
      }
    }

    var results = <Command>[];
    for (var d in data) {
      results.add(Command(d));
    }

    results.sort((first, second) => first.name.compareTo(second.name));
    return results;
  }
}

class MainPage extends StatefulWidget {
  final CommandsLoader commandsLoader;

  MainPage({Key? key, required Client client})
      : commandsLoader = CommandsLoader(client: client),
        super(key: key);

  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  CommandsLoader get commandsLoader => widget.commandsLoader;

  Widget renderer(BuildContext context, AsyncSnapshot<List<Command>> snapshot) {
    var error = snapshot.error;
    if (error != null) throw error;

    var data = snapshot.data;
    if (data == null) return loadingIndicator();

    return Flexible(
      child: ListView.builder(
        itemCount: data.length,
        itemBuilder: (context, index) => Padding(padding: const EdgeInsets.all(5.0), child: data[index].display()),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    var screenSize = MediaQuery.of(context).size;
    return Scaffold(
      body: Row(
        children: [
          SizedBox(
            width: screenSize.width / 5,
            height: screenSize.height,
            child: Container(
              color: themeColor,
              padding: const EdgeInsets.all(8.0),
              child: Column(
                children: [
                  Image.network("/favicon.png", fit: BoxFit.contain),
                  TextButton(
                    onPressed: () async {
                      await launchUrl(Uri.https("github.com", "Serious-senpai/haruka-lightweight"));
                    },
                    child: const Text("Source code", style: TextStyle(color: Colors.yellow)),
                  ),
                ],
              ),
            ),
          ),
          FutureBuilder(
            builder: renderer,
            future: commandsLoader.fetcher,
          ),
        ],
      ),
    );
  }
}
