import "package:fluttertoast/fluttertoast.dart";

class TicTacToeException implements Exception {
  final String message;

  TicTacToeException(this.message);

  Future<void> showMessage() => Fluttertoast.showToast(msg: message);
}
