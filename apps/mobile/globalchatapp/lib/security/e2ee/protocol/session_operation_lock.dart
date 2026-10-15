import 'dart:async';

/// Serializes libsignal operations per remote address (ratchet safety).
class SessionOperationLock {
  final _locks = <String, Future<void>>{};

  Future<T> run<T>(String addressKey, Future<T> Function() action) {
    final previous = _locks[addressKey] ?? Future.value();
    final completer = Completer<void>();
    _locks[addressKey] = completer.future;

    return previous.then((_) => action()).whenComplete(() {
      completer.complete();
      if (_locks[addressKey] == completer.future) {
        _locks.remove(addressKey);
      }
    });
  }
}
