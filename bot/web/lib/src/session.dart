import "dart:convert";
import "dart:html";

import "package:http/http.dart";

import "commands.dart";
import "users.dart";

final _httpClient = Client();
const LOCAL_TOKEN_KEY = "authorizationToken";

class AuthorizationState {
  final User user;
  final String token;

  AuthorizationState({
    required this.user,
    required this.token,
  });

  factory AuthorizationState.fromJson(Map<String, dynamic> data) {
    var user = User(data["user"]);
    var token = data["token"];
    return AuthorizationState(user: user, token: token);
  }

  static Future<AuthorizationState?> fromToken(String token) async {
    var response = await _httpClient.get(Uri.parse("/login"), headers: {"X-Auth-Token": token});
    var data = jsonDecode(utf8.decode(response.bodyBytes));
    if (data["success"]) {
      return AuthorizationState(user: User(data["user"]), token: token);
    }

    return null;
  }
}

/// Represent the current client session
class ClientSession {
  final _client = _httpClient;

  AuthorizationState? _authorizationState;
  bool get loggedIn => _authorizationState != null;

  /// Our current authorization state, this is null if we are not logged in
  AuthorizationState? get authorizationState => _authorizationState;
  set authorizationState(AuthorizationState? value) {
    _authorizationState = value;
    if (value != null) {
      window.localStorage[LOCAL_TOKEN_KEY] = value.token;
    } else {
      window.localStorage.remove(LOCAL_TOKEN_KEY);
    }

    onAuthorizationStateChange();
  }

  CommandsLoader? _commandsLoader;

  /// [CommandsLoader] for the current session
  CommandsLoader get commandsLoader => _commandsLoader ??= CommandsLoader(session: this);

  ClientSession._();

  /// Initialize a new [ClientSession], this should be called only once
  static Future<ClientSession> create() async {
    var object = ClientSession._();

    var token = window.localStorage[LOCAL_TOKEN_KEY];
    if (token != null) {
      object.authorizationState = await AuthorizationState.fromToken(token);
    }

    return object;
  }

  /// Attempt to login with a given login key.
  ///
  /// Return true on success, false otherwise
  Future<bool> login(String key) async {
    var headers = {"Login-Key": key};
    var response = await post(Uri.parse("/login"), headers: headers);
    var data = jsonDecode(utf8.decode(response.bodyBytes));
    if (data["success"]) {
      authorizationState = AuthorizationState.fromJson(data);
      return true;
    }

    return false;
  }

  /// Set the current [authorizationState] to null
  void logout() {
    authorizationState = null;
  }

  /// Callback to be called when our authorization state changes
  void onAuthorizationStateChange() {
    commandsLoader.refresh();
  }

  Map<String, String>? _constructHeaders(Map<String, String>? headers) {
    if (loggedIn) {
      headers = headers ?? <String, String>{};
      headers["X-Auth-Token"] = authorizationState!.token;
    }

    return headers;
  }

  /// Perform a GET request with authorization data
  Future<Response> get(Uri url, {Map<String, String>? headers}) => _client.get(url, headers: _constructHeaders(headers));

  /// Perform a POST request with authorization data
  Future<Response> post(
    Uri url, {
    Map<String, String>? headers,
    Object? body,
    Encoding? encoding,
  }) =>
      _client.post(
        url,
        headers: _constructHeaders(headers),
        body: body,
        encoding: encoding,
      );
}
