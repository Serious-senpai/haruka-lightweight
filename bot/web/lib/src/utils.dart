import "dart:html";

import "package:flutter/material.dart";
import "package:web_socket_channel/html.dart";

class WebSocketBroadcastChannel extends HtmlWebSocketChannel {
  Stream<dynamic>? _stream;

  @override
  Stream<dynamic> get stream {
    Stream<dynamic> sendEvent() async* {
      await for (var data in super.stream) {
        if (data != "PONG") yield data;
      }
    }

    return _stream ??= sendEvent().asBroadcastStream();
  }

  Future<void> sendPing() async {
    while (true) {
      sink.add("PING");
      await Future.delayed(const Duration(seconds: 15));
    }
  }

  WebSocketBroadcastChannel.connect(Uri uri, {Iterable<String>? protocols}) : super.connect(uri, protocols: protocols) {
    sendPing();
  }
}

class Notifier {
  final _notifier = ValueNotifier<bool>(true);

  Notifier();

  void addListener(void Function() callback) => _notifier.addListener(callback);
  void removeListener(void Function() callback) => _notifier.removeListener(callback);

  void notifyListeners() {
    _notifier.value = !_notifier.value;
  }
}

Uri websocketUri(String path, [Map<String, String>? query]) => Uri(
      scheme: window.location.protocol == "https:" ? "wss" : "ws",
      host: window.location.hostname,
      port: int.tryParse(window.location.port),
      path: path,
      queryParameters: query,
    );

/// Objects holding a pair of value
class Pair<T1, T2> {
  T1 first;
  T2 second;

  @override
  int get hashCode => first.hashCode ^ second.hashCode;

  Pair(this.first, this.second);

  @override
  bool operator ==(covariant Pair<T1, T2> other) => other.first == first && other.second == second;
}

String join(String part1, [String? part2]) {
  var result = part1;
  if (!result.endsWith("/")) result += "/";

  if (part2 != null && part2.startsWith("/")) {
    result += part2.substring(1);
  }

  return result;
}

Future<void> navigate({
  required BuildContext context,
  required String routeName,
}) async {
  window.history.pushState({}, "Haruka", join("/#", routeName));
  await Navigator.pushReplacementNamed(context, routeName);
}

/// A transparent [SizedBox] with a width and height of 10.0
const seperator = SizedBox(width: 10.0, height: 10.0);

/// Display an error indicator above [content]
Widget errorIndicator({String? content, double size = 60}) {
  var sizedBox = SizedBox(
    width: size,
    height: size,
    child: const Icon(Icons.error_outline),
  );

  var children = <Widget>[sizedBox];
  if (content != null) {
    children.addAll(
      [
        seperator,
        Text(content),
      ],
    );
  }

  return Column(
    mainAxisAlignment: MainAxisAlignment.center,
    children: children,
  );
}

/// Display a loading indicator above [content]
Widget loadingIndicator({String? content, double size = 60}) {
  var sizedBox = SizedBox(
    width: size,
    height: size,
    child: const CircularProgressIndicator(),
  );

  var children = <Widget>[sizedBox];
  if (content != null) {
    children.addAll(
      [
        seperator,
        Text(content),
      ],
    );
  }

  return Column(
    mainAxisAlignment: MainAxisAlignment.center,
    children: children,
  );
}
