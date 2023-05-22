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
  double get incrementRate => _incrementRate ??= _level > 0 ? baseRate * pow(2, _level) : 0;
  double? _incrementRate;

  /// Cost for upgrade
  double get upgradeCost => _upgradeCost ??= max(baseRate * pow(2.5, _level - 1), 360 * incrementRate);
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

  void reset() {
    _level = 0;
    _incrementRate = _upgradeCost = null;
    window.localStorage.remove(_lookupKey);
  }

  @override
  String toString() => "";
}
