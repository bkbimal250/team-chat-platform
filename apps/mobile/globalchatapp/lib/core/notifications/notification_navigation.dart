class NotificationNavigationPayload {
  const NotificationNavigationPayload(this.conversationId, {this.messageId});
  final String conversationId;
  final String? messageId;
  static NotificationNavigationPayload? parse(Map<String, dynamic> data) {
    final c = data['conversationId'];
    final m = data['messageId'];
    if (c is! String || c.trim().isEmpty || (m != null && m is! String)) {
      return null;
    }
    return NotificationNavigationPayload(c.trim(), messageId: m as String?);
  }

  String get key => '$conversationId:${messageId ?? ''}';
}

class NotificationNavigationCoordinator {
  final _handled = <String>{};
  NotificationNavigationPayload? accept(Map<String, dynamic> data) {
    final p = NotificationNavigationPayload.parse(data);
    return p != null && _handled.add(p.key) ? p : null;
  }
}
