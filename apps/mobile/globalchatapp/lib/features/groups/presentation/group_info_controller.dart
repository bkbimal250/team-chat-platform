import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../domain/group.dart';
import '../data/demo_group_repository.dart';
import '../domain/group_repository.dart';

final groupInfoRepositoryProvider = Provider<GroupRepository>(
  (_) => DemoGroupRepository(
    initialGroups: const [
      GroupDetails(
        id: 'engineering',
        name: 'Engineering Team',
        members: [
          GroupMember('1', 'Alice', role: GroupRole.owner),
          GroupMember('2', 'Bob', role: GroupRole.admin),
          GroupMember('3', 'Charlie'),
          GroupMember('4', 'David'),
        ],
      ),
    ],
  ),
);

class GroupInfoState {
  const GroupInfoState(
    this.group,
    this.current, {
    this.error,
    this.isMutating = false,
  });
  final GroupDetails group;
  final GroupMember current;
  final String? error;
  final bool isMutating;
  bool get canAdd =>
      current.role == GroupRole.owner || current.role == GroupRole.admin;
  bool canRemove(GroupMember target) =>
      target.id != current.id &&
      (current.role == GroupRole.owner ||
          (current.role == GroupRole.admin && target.role == GroupRole.member));
}

class GroupInfoController extends Notifier<GroupInfoState> {
  GroupRepository get _repository => ref.read(groupInfoRepositoryProvider);
  @override
  GroupInfoState build() {
    const members = [
      GroupMember('1', 'Alice', role: GroupRole.owner),
      GroupMember('2', 'Bob', role: GroupRole.admin),
      GroupMember('3', 'Charlie'),
      GroupMember('4', 'David'),
    ];
    return GroupInfoState(
      GroupDetails(
        id: 'engineering',
        name: 'Engineering Team',
        members: members,
      ),
      members[0],
    );
  }

  Future<bool> remove(GroupMember m) async {
    if (!state.canRemove(m)) return false;
    final before = state;
    state = GroupInfoState(before.group, before.current, isMutating: true);
    try {
      await _repository.removeMember(before.group.id, m.id);
      state = GroupInfoState(
        GroupDetails(
          id: state.group.id,
          name: state.group.name,
          members: state.group.members.where((x) => x.id != m.id).toList(),
        ),
        state.current,
      );
      return true;
    } catch (_) {
      state = GroupInfoState(
        before.group,
        before.current,
        error: 'Unable to remove this member right now.',
      );
      return false;
    }
  }

  Future<bool> leaveGroup() async {
    final before = state;
    state = GroupInfoState(before.group, before.current, isMutating: true);
    try {
      await _repository.leaveGroup(before.group.id, before.current.id);
      state = GroupInfoState(before.group, before.current);
      return true;
    } catch (_) {
      state = GroupInfoState(
        before.group,
        before.current,
        error: 'Unable to leave this group right now.',
      );
      return false;
    }
  }
}

final groupInfoProvider = NotifierProvider<GroupInfoController, GroupInfoState>(
  GroupInfoController.new,
);
