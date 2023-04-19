import "dart:convert";

import "package:http/http.dart";

import "commands.dart";
import "users.dart";

class AuthorizationState {
  final User user;
  final String token;

  AuthorizationState({
    required this.user,
    required this.token,
  });
}

class ClientSession {
  final _client = Client();
  late final CommandsLoader commandsLoader;

  AuthorizationState? authorizationState;

  bool get loggedIn => authorizationState != null;

  ClientSession._();

  factory ClientSession.create() {
    var object = ClientSession._();
    object.commandsLoader = CommandsLoader(session: object);
    return object;
  }

  Future<bool> logIn(String key) async {
    var headers = {"Login-Key": key};
    var response = await _client.post(Uri.parse("/login"), headers: headers);
    var data = jsonDecode(utf8.decode(response.bodyBytes));
    if (data["success"]) {
      var user = User(data["user"]!);
      var token = data["token"]!;
      authorizationState = AuthorizationState(user: user, token: token);

      commandsLoader.refresh();

      return true;
    }

    return false;
  }

  Map<String, String>? constructHeaders(Map<String, String>? headers) {
    if (loggedIn) {
      headers = headers ?? <String, String>{};
      headers["X-Auth-Token"] = authorizationState!.token;
    }

    return headers;
  }

  Future<Response> get(Uri url, {Map<String, String>? headers}) => _client.get(url, headers: constructHeaders(headers));

  Future<Response> post(
    Uri url, {
    Map<String, String>? headers,
    Object? body,
    Encoding? encoding,
  }) =>
      _client.post(
        url,
        headers: constructHeaders(headers),
        body: body,
        encoding: encoding,
      );
}
