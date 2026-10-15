import 'dart:convert';
import 'dart:typed_data';

/// Small helper for persisting id lists in secure storage (pre-key indexes).
abstract final class IntListCodec {
  static Uint8List encode(List<int> ids) =>
      Uint8List.fromList(utf8.encode(jsonEncode(ids)));

  static List<int> decode(Uint8List bytes) {
    final decoded = jsonDecode(utf8.decode(bytes));
    if (decoded is! List) return const [];
    return decoded.map((e) => (e as num).toInt()).toList();
  }
}
