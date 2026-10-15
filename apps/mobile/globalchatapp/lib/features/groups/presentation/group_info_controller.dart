import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../application/group_providers.dart';
import '../domain/group.dart';
import '../domain/group_repository.dart';

class GroupInfoState {
  const GroupInfoState({
    this.loading = false,
    this.group,
    this.current,
    this.error,
    this.isMutating = false,
    this.conversationId,
  });

  final bool loading;
  final GroupDetails? group;
  final GroupMember? current;
  final String? error;
  final bool isMutating;
  final String? conversationId;

  bool get canAdd {
    final role = current?.role ?? group?.myRole;
    return role == GroupRole.owner || role == GroupRole.admin;
  }

  bool canRemove(GroupMember target) {
    final role = current?.role ?? group?.myRole;
    if (current == null || target.id == current!.id) return false;
    if (role == GroupRole.owner) return target.role != GroupRole.owner;
    if (role == GroupRole.admin) return target.role == GroupRole.member;
    return false;
  }
}

class GroupInfoController extends Notifier<GroupInfoState> {
  GroupRepository get _repository => ref.read(groupRepositoryProvider);

  @override
  GroupInfoState build() => const GroupInfoState();

  void mount(String conversationId) {
    if (state.conversationId == conversationId && state.group != null) return;
    state = GroupInfoState(loading: true, conversationId: conversationId);
    Future.microtask(refresh);
  }

  Future<void> refresh() async {
    final conversationId = state.conversationId;
    if (conversationId == null) return;
    state = GroupInfoState(
      loading: true,
      conversationId: conversationId,
      group: state.group,
      current: state.current,
    );
    try {
      final group = await _repository.getGroup(conversationId);
      if (group == null) {
        state = GroupInfoState(
          loading: false,
          conversationId: conversationId,
          error: 'Group not found.',
        );
        return;
      }
      final self = group.members.cast<GroupMember?>().firstWhere(
            (m) => m!.role == group.myRole,
            orElse: () => group.members.isNotEmpty ? group.members.first : null,
          );
      state = GroupInfoState(
        loading: false,
        conversationId: conversationId,
        group: group,
        current: self,
      );
    } catch (_) {
      state = GroupInfoState(
        loading: false,
        conversationId: conversationId,
        error: 'Could not load group info.',
      );
    }
  }

  Future<bool> remove(GroupMember m) async {
    if (!state.canRemove(m) || state.group == null) return false;
    final before = state;
    state = GroupInfoState(
      loading: false,
      conversationId: before.conversationId,
      group: before.group,
      current: before.current,
      isMutating: true,
    );
    try {
      await _repository.removeMember(before.group!.id, m.id);
      await refresh();
      return true;
    } catch (_) {
      state = GroupInfoState(
        loading: false,
        conversationId: before.conversationId,
        group: before.group,
        current: before.current,
        error: 'Unable to remove this member right now.',
      );
      return false;
    }
  }

  Future<bool> addMembers(List<GroupMember> picked) async {
    if (!state.canAdd || state.group == null || picked.isEmpty) return false;
    final before = state;
    state = GroupInfoState(
      loading: false,
      conversationId: before.conversationId,
      group: before.group,
      current: before.current,
      isMutating: true,
    );
    try {
      await _repository.addMembers(
        before.group!.id,
        picked.map((m) => m.id).toList(),
      );
      await refresh();
      return true;
    } catch (_) {
      state = GroupInfoState(
        loading: false,
        conversationId: before.conversationId,
        group: before.group,
        current: before.current,
        error: 'Could not add members.',
      );
      return false;
    }
  }

  Future<bool> deleteGroup() async {
    final before = state;
    if (before.group == null) return false;
    if (before.group!.myRole != GroupRole.owner) return false;
    state = GroupInfoState(
      loading: false,
      conversationId: before.conversationId,
      group: before.group,
      current: before.current,
      isMutating: true,
    );
    try {
      await _repository.deleteGroup(before.group!.id);
      return true;
    } catch (_) {
      state = GroupInfoState(
        loading: false,
        conversationId: before.conversationId,
        group: before.group,
        current: before.current,
        error: 'Could not delete group.',
      );
      return false;
    }
  }

  Future<bool> promote(GroupMember member) async {
    if (state.group == null) return false;
    try {
      await _repository.promoteMember(state.group!.id, member.id);
      await refresh();
      return true;
    } catch (_) {
      state = GroupInfoState(
        loading: false,
        conversationId: state.conversationId,
        group: state.group,
        current: state.current,
        error: 'Could not promote member.',
      );
      return false;
    }
  }

  Future<bool> leaveGroup() async {
    final before = state;
    if (before.group == null || before.current == null) return false;
    state = GroupInfoState(
      loading: false,
      conversationId: before.conversationId,
      group: before.group,
      current: before.current,
      isMutating: true,
    );
    try {
      await _repository.leaveGroup(before.group!.id, before.current!.id);
      if (ref.mounted) {
        state = GroupInfoState(
          loading: false,
          conversationId: before.conversationId,
          group: before.group,
          current: before.current,
        );
      }
      return true;
    } catch (_) {
      state = GroupInfoState(
        loading: false,
        conversationId: before.conversationId,
        group: before.group,
        current: before.current,
        error: 'Unable to leave this group right now.',
      );
      return false;
    }
  }
}

final groupInfoProvider =
    NotifierProvider.autoDispose<GroupInfoController, GroupInfoState>(
  GroupInfoController.new,
);
