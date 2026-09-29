import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:globalchatapp/features/groups/data/demo_group_repository.dart';
import 'package:globalchatapp/features/groups/domain/group.dart';
import 'package:globalchatapp/features/groups/domain/group_repository.dart';
import 'package:globalchatapp/features/groups/presentation/group_info_controller.dart';

class _Repository implements GroupRepository {
  _Repository({this.failRemove = false, this.failLeave = false});
  final bool failRemove, failLeave;
  int removeCalls = 0, leaveCalls = 0;
  @override
  Future<GroupDetails> createGroup(String n, List<GroupMember> m) async =>
      GroupDetails(id: 'x', name: n, members: m);
  @override
  Future<GroupDetails?> getGroup(String id) async => null;
  @override
  Future<void> removeMember(String g, String m) async {
    removeCalls++;
    if (failRemove) throw StateError('fail');
  }

  @override
  Future<void> leaveGroup(String g, String m) async {
    leaveCalls++;
    if (failLeave) throw StateError('fail');
  }

  @override
  Future<List<GroupMember>> searchMembers(String q) async => [];
}

void main() {
  ProviderContainer container(_Repository repo) => ProviderContainer(
    overrides: [groupInfoRepositoryProvider.overrideWithValue(repo)],
  );
  test('remove member failure preserves member', () async {
    final repo = _Repository(failRemove: true);
    final c = container(repo);
    addTearDown(c.dispose);
    final before = c.read(groupInfoProvider);
    final ok = await c
        .read(groupInfoProvider.notifier)
        .remove(before.group.members.last);
    final after = c.read(groupInfoProvider);
    expect(ok, isFalse);
    expect(repo.removeCalls, 1);
    expect(after.group.members.length, before.group.members.length);
    expect(after.error, isNotNull);
    expect(after.isMutating, isFalse);
  });
  test('demo leave mutation persists on fresh read', () async {
    const group = GroupDetails(
      id: 'g',
      name: 'G',
      members: [
        GroupMember('1', 'Owner', role: GroupRole.owner),
        GroupMember('2', 'Leaving'),
        GroupMember('3', 'Other'),
      ],
    );
    final repo = DemoGroupRepository(initialGroups: [group]);
    await repo.leaveGroup('g', '2');
    final fresh = await repo.getGroup('g');
    expect(fresh!.members.map((m) => m.id), ['1', '3']);
  });
  test('leave controller success calls repository once', () async {
    final repo = _Repository();
    final c = container(repo);
    addTearDown(c.dispose);
    final ok = await c.read(groupInfoProvider.notifier).leaveGroup();
    expect(ok, isTrue);
    expect(repo.leaveCalls, 1);
    expect(c.read(groupInfoProvider).error, isNull);
    expect(c.read(groupInfoProvider).isMutating, isFalse);
  });
  test('leave controller failure preserves state', () async {
    final repo = _Repository(failLeave: true);
    final c = container(repo);
    addTearDown(c.dispose);
    final before = c.read(groupInfoProvider);
    final ok = await c.read(groupInfoProvider.notifier).leaveGroup();
    final after = c.read(groupInfoProvider);
    expect(ok, isFalse);
    expect(repo.leaveCalls, 1);
    expect(after.group.members.length, before.group.members.length);
    expect(after.isMutating, isFalse);
    expect(after.error, isNotNull);
  });
}
