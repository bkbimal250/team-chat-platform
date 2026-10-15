import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:globalchatapp/features/groups/application/group_providers.dart';
import 'package:globalchatapp/features/groups/domain/group.dart';
import 'package:globalchatapp/features/groups/domain/group_repository.dart';
import 'package:globalchatapp/features/groups/presentation/group_info_controller.dart';

class _FakeRepo implements GroupRepository {
  _FakeRepo(this.group);
  GroupDetails group;
  int removeCalls = 0;

  @override
  Future<List<GroupMember>> searchMembers(String query) async => group.members;

  @override
  Future<GroupDetails> createGroup(String name, List<GroupMember> members) async =>
      group;

  @override
  Future<GroupDetails?> getGroup(String id) async => group;

  @override
  Future<void> addMembers(String groupId, List<String> memberIds) async {}

  @override
  Future<void> removeMember(String groupId, String memberId) async {
    removeCalls++;
    group = GroupDetails(
      id: group.id,
      name: group.name,
      members: group.members.where((m) => m.id != memberId).toList(),
      myRole: group.myRole,
    );
  }

  @override
  Future<void> leaveGroup(String groupId, String memberId) async {}

  @override
  Future<void> deleteGroup(String groupId) async {}

  @override
  Future<void> promoteMember(String groupId, String memberId) async {}

  @override
  Future<void> demoteMember(String groupId, String memberId) async {}
}

void main() {
  test('remove member success', () async {
    const members = [
      GroupMember('1', 'Owner', role: GroupRole.owner),
      GroupMember('2', 'Bob'),
      GroupMember('3', 'Charlie'),
    ];
    final repo = _FakeRepo(
      GroupDetails(id: 'g1', name: 'Test', members: members, myRole: GroupRole.owner),
    );
    final container = ProviderContainer(
      overrides: [groupRepositoryProvider.overrideWithValue(repo)],
    );
    container.listen(groupInfoProvider, (_, _) {});
    addTearDown(container.dispose);
    final controller = container.read(groupInfoProvider.notifier);
    controller.mount('g1');
    await Future<void>.delayed(const Duration(milliseconds: 50));

    final before = container.read(groupInfoProvider);
    final target = before.group!.members.last;
    final result = await controller.remove(target);
    final after = container.read(groupInfoProvider);

    expect(result, isTrue);
    expect(after.group!.members.length, before.group!.members.length - 1);
    expect(after.group!.members.any((m) => m.id == target.id), isFalse);
  });

  test('leave calls repository', () async {
    final repo = _FakeRepo(
      const GroupDetails(
        id: 'g1',
        name: 'Test',
        members: [GroupMember('1', 'Owner', role: GroupRole.owner)],
        myRole: GroupRole.owner,
      ),
    );
    var left = false;
    final tracking = _TrackingLeave(repo, () => left = true);
    final container = ProviderContainer(
      overrides: [groupRepositoryProvider.overrideWithValue(tracking)],
    );
    container.listen(groupInfoProvider, (_, _) {});
    addTearDown(container.dispose);
    final controller = container.read(groupInfoProvider.notifier);
    controller.mount('g1');
    await Future<void>.delayed(Duration.zero);
    final current = container.read(groupInfoProvider).current!;
    final result = await controller.leaveGroup();
    expect(result, isTrue);
    expect(left, isTrue);
  });
}

class _TrackingLeave implements GroupRepository {
  _TrackingLeave(this.inner, this.onLeave);
  final GroupRepository inner;
  final void Function() onLeave;

  @override
  Future<List<GroupMember>> searchMembers(String q) => inner.searchMembers(q);
  @override
  Future<GroupDetails> createGroup(String n, List<GroupMember> m) =>
      inner.createGroup(n, m);
  @override
  Future<GroupDetails?> getGroup(String id) => inner.getGroup(id);
  @override
  Future<void> addMembers(String g, List<String> ids) => inner.addMembers(g, ids);
  @override
  Future<void> removeMember(String g, String m) => inner.removeMember(g, m);
  @override
  Future<void> leaveGroup(String g, String m) async {
    onLeave();
    return inner.leaveGroup(g, m);
  }
  @override
  Future<void> deleteGroup(String g) => inner.deleteGroup(g);
  @override
  Future<void> promoteMember(String g, String m) => inner.promoteMember(g, m);
  @override
  Future<void> demoteMember(String g, String m) => inner.demoteMember(g, m);
}
