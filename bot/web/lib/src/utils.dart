import "package:flutter/material.dart";

class Notifier {
  final _notifier = ValueNotifier<bool>(true);

  Notifier();

  void addListener(VoidCallback callback) => _notifier.addListener(callback);
  void removeListener(VoidCallback callback) => _notifier.removeListener(callback);

  void notifyListeners() {
    _notifier.value = !_notifier.value;
  }
}

/// A transparent [SizedBox] with a width and height of 10.0
const seperator = SizedBox(width: 10.0, height: 10.0);

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
