import "package:flutter/material.dart";

import "template.dart";
import "../src/commands.dart";
import "../src/environment.dart";
import "../src/session.dart";
import "../src/utils.dart";

class MainPage extends StatefulWidget {
  final ClientSession _http;

  const MainPage({Key? key, required ClientSession session})
      : _http = session,
        super(key: key);

  @override
  State<MainPage> createState() => _MainPageState();
}

class _MainPageState extends State<MainPage> {
  final _searchController = TextEditingController();

  CommandsLoader get commandsLoader => widget._http.commandsLoader;

  Size get screenSize => MediaQuery.of(context).size;

  void refresh() => setState(() {});

  Widget renderer(BuildContext context, AsyncSnapshot<List<Command>> snapshot) {
    var error = snapshot.error;
    if (error != null) throw error;

    var data = snapshot.data;
    if (data == null) {
      return SizedBox(
        width: screenSize.width * 4 / 5,
        height: screenSize.height,
        child: Center(child: loadingIndicator()),
      );
    }

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
  void initState() {
    commandsLoader.notifier.addListener(refresh);
    super.initState();
  }

  @override
  void dispose() {
    commandsLoader.notifier.removeListener(refresh);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => TemplateScaffold(
        session: widget._http,
        child: FutureBuilder(
          builder: renderer,
          future: commandsLoader.fetcher,
        ),
      );
}
