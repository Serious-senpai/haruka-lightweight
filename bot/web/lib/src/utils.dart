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

String join(
  String part1, [
  String? part2,
  String? part3,
  String? part4,
  String? part5,
  String? part6,
  String? part7,
  String? part8,
  String? part9,
  String? part10,
  String? part11,
  String? part12,
  String? part13,
  String? part14,
  String? part15,
  String? part16,
  String? part17,
  String? part18,
  String? part19,
]) {
  var result = part1;
  if (!result.endsWith("/")) result += "/";

  var parts = [
    part2,
    part3,
    part4,
    part5,
    part6,
    part7,
    part8,
    part9,
    part10,
    part11,
    part12,
    part13,
    part14,
    part15,
    part16,
    part17,
    part18,
    part19,
  ];
  for (var part in parts) {
    if (part == null) break;
    if (part.startsWith("/")) part = part.substring(1);

    result += part;
    if (!result.endsWith("/")) result += "/";
  }

  return result;
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
