import 'package:flutter_test/flutter_test.dart';
import 'package:globalchatapp/core/notifications/notification_navigation.dart';

void main() {
  test('accepts a conversation payload', () {
    expect(
      NotificationNavigationPayload.parse({'conversationId': 'c1'})
          ?.conversationId,
      'c1',
    );
  });
  test('rejects malformed payload', () {
    expect(NotificationNavigationPayload.parse({'messageId': 'm'}), isNull);
  });
  test('deduplicates payloads', () {
    final c = NotificationNavigationCoordinator();
    expect(c.accept({'conversationId': 'c1'}), isNotNull);
    expect(c.accept({'conversationId': 'c1'}), isNull);
    expect(c.accept({'conversationId': 'c2'}), isNotNull);
  });
}
