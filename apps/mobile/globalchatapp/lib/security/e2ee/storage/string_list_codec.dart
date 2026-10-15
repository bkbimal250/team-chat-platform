import 'dart:convert';
import 'dart:typed_data';

abstract final class StringListCodec {
  static Uint8List encode(List<String> values) =>
      Uint8List.fromList(utf8.encode(jsonEncode(values)));

  static List<String> decode(Uint8List bytes) {
    final decoded = jsonDecode(utf8.decode(bytes));
    if (decoded is! List) return const [];
    return decoded.map((e) => e.toString()).toList();
  }
}
