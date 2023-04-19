import "dart:convert";

import "package:flutter/material.dart";
import "package:flutter_markdown/flutter_markdown.dart";

import "environment.dart";
import "session.dart";

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
              const Text("Aliases ", style: TextStyle(fontWeight: FontWeight.bold, fontStyle: FontStyle.italic)),
              MarkdownBody(data: List<String>.generate(aliases.length, (index) => "`${aliases[index]}`").join(", ")),
            ],
          ),
          Row(
            children: [
              const Text("Syntax ", style: TextStyle(fontWeight: FontWeight.bold, fontStyle: FontStyle.italic)),
              MarkdownBody(data: "```\n$usage\n```"),
            ],
          ),
          Row(
            children: [
              const Text("Description ", style: TextStyle(fontWeight: FontWeight.bold, fontStyle: FontStyle.italic)),
              MarkdownBody(data: description),
            ],
          ),
        ],
      );
}

class CommandsLoader {
  final ClientSession _http;
  Future<List<Command>>? _fetcher;

  Future<List<Command>> get fetcher => _fetcher ??= _fetchCommands();

  final notifier = ValueNotifier<bool>(true);

  CommandsLoader({required ClientSession session}) : _http = session;

  void refresh() {
    _fetcher = null;
    notifier.value = !notifier.value;
  }

  Future<List<Command>> _fetchCommands() async {
    var response = await _http.get(Uri.parse("/commands"));
    var data = List<Map<String, dynamic>>.from(jsonDecode(utf8.decode(response.bodyBytes)));

    var results = List<Command>.generate(data.length, (index) => Command(data[index]));
    results.sort((first, second) => first.name.compareTo(second.name));
    return results;
  }
}
