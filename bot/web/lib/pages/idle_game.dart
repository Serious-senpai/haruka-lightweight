import "package:flutter/material.dart";

import "template.dart";
import "../src/session.dart";
import "../src/utils.dart";
import "../src/idle_game/errors.dart";
import "../src/idle_game/state.dart";

class IdleGamePage extends StatefulWidget {
  final ClientSession _http;

  const IdleGamePage({Key? key, required ClientSession session})
      : _http = session,
        super(key: key);

  @override
  State<IdleGamePage> createState() => _IdleGamePageState();
}

class _IdleGamePageState extends State<IdleGamePage> {
  final state = GameState.instance;
  Size get screenSize => MediaQuery.of(context).size;

  @override
  void initState() {
    state.active = true;
    super.initState();
  }

  @override
  void deactivate() {
    state.active = false;
    super.deactivate();
  }

  @override
  Widget build(BuildContext context) => TemplateScaffold(
        session: widget._http,
        child: StreamBuilder(
          initialData: state,
          stream: state.stream,
          builder: (context, snapshot) {
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

            return Padding(
              padding: const EdgeInsets.all(8.0),
              child: Row(
                children: [
                  Expanded(
                    flex: 3,
                    child: Stack(
                      children: [
                        Center(
                          child: GestureDetector(
                            onTap: state.click,
                            child: const Icon(Icons.monetization_on_outlined, size: 160.0),
                          ),
                        ),
                        Positioned(
                          top: 1.0,
                          right: 1.0,
                          child: Text("💲${state.coins.floor()}"),
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    flex: 2,
                    child: Column(
                      children: [
                        SizedBox(
                          height: 30.0,
                          child: RichText(
                            text: const TextSpan(
                              children: [
                                WidgetSpan(
                                  child: Icon(Icons.store_outlined),
                                  baseline: TextBaseline.alphabetic,
                                  style: TextStyle(color: Colors.white, fontSize: 14.0),
                                ),
                                TextSpan(
                                  text: "SHOP",
                                  style: TextStyle(color: Colors.white, fontSize: 14.0),
                                ),
                              ],
                            ),
                          ),
                        ),
                        SizedBox(
                          height: screenSize.height - 30.0,
                          child: ListView.builder(
                            itemCount: state.items.length + 1,
                            itemBuilder: (context, index) {
                              if (index == 0) {
                                return ListTile(
                                  leading: const Icon(Icons.ads_click_outlined),
                                  title: const Text("Coins per click"),
                                  subtitle: Text("Lv.${state.level} (💲${state.coinsRate.floor()}/click)"),
                                  trailing: Column(
                                    children: [
                                      Text("💲${state.upgradeCost.ceil()}"),
                                      const Text("UPGRADE"),
                                    ],
                                  ),
                                  onTap: () async {
                                    try {
                                      state.upgrade();
                                    } on IdleGameException catch (e) {
                                      await e.showMessage();
                                    }
                                  },
                                );
                              }
                              var item = state.items[index - 1];
                              return ListTile(
                                leading: const Icon(Icons.precision_manufacturing_outlined),
                                title: Text(item.name),
                                subtitle: Text(item.level == 0 ? "Purchase" : "Lv.${item.level} (💲${item.incrementRate.floor()}/s)"),
                                trailing: Column(
                                  children: [
                                    Text("💲${item.upgradeCost.ceil()}"),
                                    const Text("UPGRADE"),
                                  ],
                                ),
                                onTap: () async {
                                  try {
                                    item.upgrade();
                                  } on IdleGameException catch (e) {
                                    await e.showMessage();
                                  }
                                },
                              );
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      );
}
