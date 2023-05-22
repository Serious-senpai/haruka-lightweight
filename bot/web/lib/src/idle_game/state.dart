import "dart:html";
import "dart:math";

import "package:async_locks/async_locks.dart";

import "errors.dart";
import "items.dart";

/// A singleton of the current game state
class GameState {
  static const _coinsKey = "idle-coins";
  static const _levelKey = "idle-level";
  static const _resetKey = "idle-reset-count";

  static final instance = GameState._();

  /// All current [Item]s
  List<Item> get items => _items ??= [
        Item(0, "Common Miner", 5, state: this),
        Item(1, "Rare Miner", 100, state: this),
        Item(2, "Epic Miner", 2500, state: this),
        Item(3, "Elite Miner", 1000000, state: this),
        Item(4, "Super Rare Miner", 3200000, state: this),
        Item(5, "Ultra Rare Miner", 512000000, state: this),
      ];
  List<Item>? _items;

  double _coins;
  int _level;

  /// Coins gained per click
  double get coinsRate => _coinsRate ??= pow(3, _level - 1).toDouble();
  double? _coinsRate;

  /// Cost to upgrade player to the next level
  double get upgradeCost => _upgradeCost ??= coinsRate * (1 + 2 * max(15, _level));
  double? _upgradeCost;

  /// Current amount of coins
  double get coins => _coins;

  /// The player level
  int get level => _level;

  int _resetCount = 0;

  /// Number of reset made
  int get resetCount => _resetCount;

  /// Whether the game is currently active
  ///
  /// Set this to `false` will pause the game
  bool active = true;

  final _updateEvent = Event();
  Stream<GameState> _selfStream() async* {
    while (true) {
      yield this;
      await _updateEvent.wait();
      _updateEvent.clear();
    }
  }

  /// Tell [stream] to emit the current state
  void update() => _updateEvent.set();

  /// A broadcast [Stream] of the current [GameState]
  Stream<GameState> get stream => _stream ??= _selfStream().asBroadcastStream();
  Stream<GameState>? _stream;

  GameState._()
      : _coins = double.tryParse(window.localStorage[_coinsKey] ?? "0") ?? 0,
        _level = int.tryParse(window.localStorage[_levelKey] ?? "1") ?? 1 {
    assert(items.isNotEmpty);
  }

  void click() => addCoins(coinsRate);

  void addCoins(double amount) {
    if (active && amount > 0) {
      _coins += amount;
      window.localStorage[_coinsKey] = _coins.toString();
      update();
    }
  }

  void spendCoins(double amount) {
    if (active) {
      if (_coins < amount) throw IdleGameException("Not enough coins!");

      _coins -= amount;
      window.localStorage[_coinsKey] = _coins.toString();
      update();
    }
  }

  /// Level up the player
  void upgrade() {
    spendCoins(upgradeCost);
    _level++;
    _coinsRate = _upgradeCost = null;
    // Yes, we use local storage. Feel free to hack it.
    window.localStorage[_levelKey] = _level.toString();
    update();
  }

  void reset() {
    active = false;
    _coins = 0;
    _level = 1;
    _resetCount++;
    window.localStorage[_coinsKey] = _coins.toString();
    window.localStorage[_levelKey] = _level.toString();
    window.localStorage[_resetKey] = _resetCount.toString();

    _coinsRate = _upgradeCost = null;

    for (var item in items) {
      item.reset();
    }

    active = true;
    update();
  }
}
