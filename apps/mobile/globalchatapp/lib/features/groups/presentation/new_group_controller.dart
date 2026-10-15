import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../application/group_providers.dart';
import '../domain/group.dart';
import '../domain/group_repository.dart';

class NewGroupState {
  const NewGroupState({
    this.query = '',
    this.members = const [],
    this.selected = const [],
    this.step = 0,
    this.name = '',
    this.loading = false,
    this.error,
  });
  final String query, name;
  final List<GroupMember> members, selected;
  final int step;
  final bool loading;
  final String? error;
  NewGroupState copyWith({
    String? query,
    String? name,
    List<GroupMember>? members,
    List<GroupMember>? selected,
    int? step,
    bool? loading,
    String? error,
    bool clearError = false,
  }) =>
      NewGroupState(
        query: query ?? this.query,
        name: name ?? this.name,
        members: members ?? this.members,
        selected: selected ?? this.selected,
        step: step ?? this.step,
        loading: loading ?? this.loading,
        error: clearError ? null : (error ?? this.error),
      );
}

class NewGroupController extends Notifier<NewGroupState> {
  GroupRepository get _repository => ref.read(groupRepositoryProvider);

  @override
  NewGroupState build() {
    Future.microtask(() => _loadMembers(''));
    return const NewGroupState();
  }

  Future<void> _loadMembers(String q) async {
    try {
      final members = await _repository.searchMembers(q);
      state = state.copyWith(members: members, clearError: true);
    } catch (e) {
      state = state.copyWith(error: 'Could not load contacts.');
    }
  }

  void search(String q) {
    state = state.copyWith(query: q);
    _loadMembers(q);
  }

  void toggle(GroupMember m) {
    final x = [...state.selected];
    x.any((v) => v.id == m.id) ? x.removeWhere((v) => v.id == m.id) : x.add(m);
    state = state.copyWith(selected: x, clearError: true);
  }

  void details() => state.selected.isEmpty
      ? state = state.copyWith(error: 'Select at least one member')
      : state = state.copyWith(step: 1, clearError: true);
  void back() => state = state.copyWith(step: 0);
  void setName(String n) => state = state.copyWith(name: n, clearError: true);

  Future<GroupDetails?> create() async {
    if (state.name.trim().isEmpty) {
      state = state.copyWith(error: 'Enter a group name');
      return null;
    }
    state = state.copyWith(loading: true, clearError: true);
    try {
      final group = await _repository.createGroup(
        state.name.trim(),
        state.selected,
      );
      state = state.copyWith(loading: false);
      return group;
    } catch (e) {
      state = state.copyWith(
        loading: false,
        error: 'Could not create group. Check members and try again.',
      );
      return null;
    }
  }
}

final newGroupProvider = NotifierProvider<NewGroupController, NewGroupState>(
  NewGroupController.new,
);
