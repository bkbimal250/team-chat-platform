import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:globalchatapp/features/groups/application/group_providers.dart';
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
  Future<GroupDetails?> getGroup(String id) async => const GroupDetails(
        id: 'g',
        name: 'G',
        members: [
          GroupMember('1', 'Owner', role: GroupRole.owner),
          GroupMember('2', 'Bob'),
          GroupMember('3', 'Charlie'),
        ],
        myRole: GroupRole.owner,
      );

  @override
  Future<List<GroupMember>> searchMembers(String q) async => [];

  @override
  Future<void> addMembers(String groupId, List<String> memberIds) async {}

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
  Future<void> deleteGroup(String groupId) async {}

  @override
  Future<void> promoteMember(String groupId, String memberId) async {}

  @override
  Future<void> demoteMember(String groupId, String memberId) async {}
}

void main() {
  ProviderContainer container(_Repository repo) {
    final c = ProviderContainer(
      overrides: [groupRepositoryProvider.overrideWithValue(repo)],
    );
    c.listen(groupInfoProvider, (_, _) {});
    return c;
  }

  test('remove member failure preserves member', () async {
    final repo = _Repository(failRemove: true);
    final c = container(repo);
    addTearDown(c.dispose);
    final controller = c.read(groupInfoProvider.notifier);
    controller.mount('g');
    await Future<void>.delayed(Duration.zero);
    final before = c.read(groupInfoProvider);
    final ok = await controller.remove(before.group!.members.last);
    final after = c.read(groupInfoProvider);
    expect(ok, isFalse);
    expect(repo.removeCalls, 1);
    expect(after.group!.members.length, before.group!.members.length);
    expect(after.error, isNotNull);
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
    final controller = c.read(groupInfoProvider.notifier);
    controller.mount('g');
    await Future<void>.delayed(Duration.zero);
    final ok = await controller.leaveGroup();
    expect(ok, isTrue);
    expect(repo.leaveCalls, 1);
  });
}
