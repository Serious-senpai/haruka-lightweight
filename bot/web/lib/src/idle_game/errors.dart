import "package:fluttertoast/fluttertoast.dart";

class IdleGameException implements Exception {
  final String message;

  IdleGameException(this.message);

  Future<void> showMessage() => Fluttertoast.showToast(msg: message);
}
