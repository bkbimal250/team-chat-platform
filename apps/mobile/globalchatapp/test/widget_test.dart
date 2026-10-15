// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:globalchatapp/app/app.dart';

void main() {
  testWidgets('GlobalChat opens its login screen', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: GlobalChatApp()));
    await tester.pump(const Duration(milliseconds: 700));
    await tester.pumpAndSettle();
    expect(find.text('GlobalChat'), findsWidgets);
    expect(find.text('Work email or phone'), findsOneWidget);
  });
}
