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
              const Text("Syntax ", style: TextStyle(fontWeight: FontWeight.bold, fontStyle: FontStyle.italic)),
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
      data = List<Map<String, dynamic>>.generate(
        100,
        (index) => {
          "name": "name$index",
          "aliases": ["alias_1", "alias_2", "alias_3"],
          "brief": "category.name$index",
          "description": "description$index `markdown`",
          "usage": "\$name$index <param>",
        },
      );
    }

    var results = List<Command>.generate(data.length, (index) => Command(data[index]));
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
  final _searchController = TextEditingController();

  CommandsLoader get commandsLoader => widget.commandsLoader;

  void refresh() => setState(() {});

  Widget renderer(BuildContext context, AsyncSnapshot<List<Command>> snapshot) {
    var error = snapshot.error;
    if (error != null) throw error;

    var data = snapshot.data;
    if (data == null) return loadingIndicator();

    var display = <Widget>[
      const Text(
        "TEXT COMMANDS LIST",
        style: TextStyle(
          color: themeColor,
          fontSize: 30,
          fontWeight: FontWeight.bold,
        ),
      ),
      TextField(
        controller: _searchController,
        decoration: InputDecoration(
          hintText: "Press Enter to search",
          suffixIcon: IconButton(
            onPressed: () {
              _searchController.clear();
              refresh();
            },
            icon: const Icon(Icons.clear),
          ),
        ),
        autocorrect: false,
        maxLength: 50,
        onSubmitted: (value) => refresh(),
      ),
    ];

    return Flexible(
      child: ListView.builder(
        padding: const EdgeInsets.all(10.0),
        itemCount: data.length + display.length,
        itemBuilder: (context, index) => index < display.length
            ? display[index]
            : data[index - display.length].name.contains(_searchController.text)
                ? Padding(padding: const EdgeInsets.all(3.0), child: data[index - display.length].display())
                : const SizedBox.shrink(),
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
                  seperator,
                  TextButton(
                    onPressed: () async {
                      await launchUrl(Uri.https("github.com", "Serious-senpai/haruka-lightweight"));
                    },
                    child: const Text("Source code", style: TextStyle(fontSize: 20, color: Colors.yellow)),
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
