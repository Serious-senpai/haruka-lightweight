import "dart:html";
import "dart:math";

import "state.dart";

class Item {
  // The item ID
  final int id;

  /// The item name
  final String name;

  int _level = 0;

  /// Item level
  int get level => _level;

  /// Base increment rate
  final double baseRate;

  /// Increment per second
  double get incrementRate => _incrementRate ??= (pow(1.4, _level) - 1) / 0.4 * baseRate;
  double? _incrementRate;

  /// Cost for upgrade
  double get upgradeCost => _upgradeCost ??= (pow(5, _level + 1) - 1) / 4 * baseRate;
  double? _upgradeCost;

  String get _lookupKey => "idle-item-$id";
  final GameState _state;

  /// Declare a new item type
  Item(this.id, this.name, this.baseRate, {required GameState state}) : _state = state {
    _level = int.tryParse(window.localStorage[_lookupKey] ?? "0") ?? 0;
    _loop();
  }

  Future<void> _loop() async {
    while (true) {
      _state.addCoins(incrementRate);
      await Future.delayed(const Duration(seconds: 1));
    }
  }

  /// Level up the item
  void upgrade() {
    _state.spendCoins(upgradeCost);
    _level++;
    _incrementRate = _upgradeCost = null;

    window.localStorage[_lookupKey] = _level.toString();
    _state.update();
  }

  @override
  String toString() => "";
}
