import 'dart:convert';

/// JSON plaintext carried inside Signal ciphertext (never sent to REST as text).
class E2eeMessagePayload {
  const E2eeMessagePayload({
    required this.body,
    this.replyPreview,
    this.media,
    this.edited = false,
  });

  final String body;
  final String? replyPreview;
  final Map<String, dynamic>? media;
  final bool edited;

  Map<String, dynamic> toJson() => {
        'v': 1,
        'body': body,
        if (replyPreview != null) 'reply_preview': replyPreview,
        if (media != null) 'media': media,
        if (edited) 'edited': true,
      };

  factory E2eeMessagePayload.fromJson(Map<String, dynamic> json) =>
      E2eeMessagePayload(
        body: json['body'] as String? ?? '',
        replyPreview: json['reply_preview'] as String?,
        media: json['media'] as Map<String, dynamic>?,
        edited: json['edited'] as bool? ?? false,
      );

  List<int> encode() => utf8.encode(jsonEncode(toJson()));

  static E2eeMessagePayload decode(List<int> bytes) =>
      E2eeMessagePayload.fromJson(
        jsonDecode(utf8.decode(bytes)) as Map<String, dynamic>,
      );
}
