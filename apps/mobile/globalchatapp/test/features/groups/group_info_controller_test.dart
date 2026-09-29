import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:globalchatapp/features/groups/presentation/group_info_controller.dart';

void main() {
  test('remove member success', () async {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    final controller = container.read(groupInfoProvider.notifier);
    final before = container.read(groupInfoProvider);
    final target = before.group.members.last;

    final result = await controller.remove(target);
    final after = container.read(groupInfoProvider);

    expect(result, isTrue);
    expect(after.group.members.length, before.group.members.length - 1);
    expect(
      after.group.members.any((member) => member.id == target.id),
      isFalse,
    );
    expect(after.isMutating, isFalse);
    expect(after.error, isNull);
  });

  test('leave controller succeeds for the composed demo group', () async {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    final controller = container.read(groupInfoProvider.notifier);

    final result = await controller.leaveGroup();

    final state = container.read(groupInfoProvider);
    expect(result, isTrue);
    expect(state.isMutating, isFalse);
    expect(state.error, isNull);
  });
}
