import "package:flutter/material.dart";
import "package:fluttertoast/fluttertoast.dart";
import "package:url_launcher/url_launcher.dart";

import "../src/environment.dart";
import "../src/session.dart";
import "../src/utils.dart";

class TemplateScaffold extends StatefulWidget {
  final Widget child;
  final ClientSession _http;

  const TemplateScaffold({Key? key, required this.child, required ClientSession session})
      : _http = session,
        super(key: key);

  @override
  State<TemplateScaffold> createState() => _TemplateScaffoldState();
}

class _TemplateScaffoldState extends State<TemplateScaffold> {
  Widget get child => widget.child;
  ClientSession get _http => widget._http;

  void refresh() => setState(() {});

  @override
  Widget build(BuildContext context) {
    var screenSize = MediaQuery.of(context).size;
    return Scaffold(
      backgroundColor: Colors.black,
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
                  Align(
                    alignment: Alignment.topLeft,
                    child: _http.loggedIn
                        ? ExpansionTile(
                            textColor: Colors.black,
                            collapsedTextColor: Colors.black,
                            expandedAlignment: Alignment.centerRight,
                            title: Row(
                              children: [
                                _http.authorizationState!.user.displayAvatar(),
                                seperator,
                                Text(_http.authorizationState!.user.displayName),
                              ],
                            ),
                            children: [
                              TextButton(
                                onPressed: () {
                                  _http.logout();
                                  refresh();
                                },
                                child: RichText(
                                  text: const TextSpan(
                                    children: [
                                      WidgetSpan(
                                        child: Icon(
                                          Icons.logout_outlined,
                                          size: 16.0,
                                          color: Colors.black,
                                        ),
                                      ),
                                      TextSpan(
                                        text: " Logout",
                                        style: TextStyle(color: Colors.black, fontSize: 16.0),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          )
                        : TextButton(
                            onPressed: () async {
                              var key = await showDialog<String>(
                                context: context,
                                builder: (context) {
                                  var textController = TextEditingController();
                                  return AlertDialog(
                                    content: TextField(
                                      controller: textController,
                                      decoration: const InputDecoration(hintText: "Use /otp to get login OTP"),
                                      autofocus: true,
                                      maxLength: 50,
                                      onSubmitted: (value) {
                                        Navigator.pop(context, value);
                                      },
                                    ),
                                    actions: [
                                      TextButton(
                                        onPressed: () {
                                          Navigator.pop(context, textController.text);
                                        },
                                        child: const Text("OK"),
                                      ),
                                    ],
                                  );
                                },
                              );

                              if (key != null) {
                                if (await _http.login(key)) {
                                  var user = _http.authorizationState!.user;
                                  refresh();
                                  await Fluttertoast.showToast(msg: "Welcome, ${user.displayName}!");
                                } else {
                                  await Fluttertoast.showToast(msg: "Invalid password");
                                }
                              }
                            },
                            child: const Text("Login", style: TextStyle(fontSize: 20, color: Colors.black)),
                          ),
                  ),
                  seperator,
                  Image.network("/favicon.png", fit: BoxFit.contain),
                  seperator,
                  TextButton(
                    onPressed: () async {
                      await launchUrl(Uri.https("github.com", "Serious-senpai/haruka-lightweight"));
                    },
                    child: const Text("Source code", style: TextStyle(fontSize: 20, color: Colors.black)),
                  ),
                  seperator,
                  TextButton(
                    onPressed: () async {
                      await launchUrl(Uri.parse("/invite"));
                    },
                    child: const Text("Invite URL", style: TextStyle(fontSize: 20, color: Colors.black)),
                  ),
                ],
              ),
            ),
          ),
          child,
        ],
      ),
    );
  }
}
