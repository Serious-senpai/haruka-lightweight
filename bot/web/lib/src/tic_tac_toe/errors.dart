import "package:flutter/material.dart";
import "package:fluttertoast/fluttertoast.dart";

class TicTacToeException implements Exception {
  final String message;

  TicTacToeException(this.message);

  Future<void> showMessage() => Fluttertoast.showToast(
        msg: message,
        timeInSecForIosWeb: 5,
        gravity: ToastGravity.TOP_RIGHT,
        backgroundColor: Colors.red,
        textColor: Colors.black,
      );
}
