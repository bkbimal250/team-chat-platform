import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/demo_group_repository.dart';
import '../domain/group.dart';
import '../domain/group_repository.dart';

final groupRepositoryProvider = Provider<GroupRepository>(
  (_) => DemoGroupRepository(),
);

class NewGroupState {
  const NewGroupState({
    this.query = '',
    this.members = const [],
    this.selected = const [],
    this.step = 0,
    this.name = '',
    this.error,
  });
  final String query, name;
  final List<GroupMember> members, selected;
  final int step;
  final String? error;
  NewGroupState copyWith({
    String? query,
    String? name,
    List<GroupMember>? members,
    List<GroupMember>? selected,
    int? step,
    String? error,
  }) => NewGroupState(
    query: query ?? this.query,
    name: name ?? this.name,
    members: members ?? this.members,
    selected: selected ?? this.selected,
    step: step ?? this.step,
    error: error,
  );
}

class NewGroupController extends Notifier<NewGroupState> {
  @override
  NewGroupState build() {
    final all = DemoGroupRepository.members;
    return NewGroupState(members: all);
  }

  void search(String q) {
    state = state.copyWith(
      query: q,
      members: DemoGroupRepository.members
          .where((m) => m.name.toLowerCase().contains(q.toLowerCase()))
          .toList(),
    );
  }

  void toggle(GroupMember m) {
    final x = [...state.selected];
    x.any((v) => v.id == m.id) ? x.removeWhere((v) => v.id == m.id) : x.add(m);
    state = state.copyWith(selected: x);
  }

  void details() => state.selected.isEmpty
      ? state = state.copyWith(error: 'Select at least one member')
      : state = state.copyWith(step: 1, error: null);
  void back() => state = state.copyWith(step: 0);
  void setName(String n) => state = state.copyWith(name: n, error: null);
  Future<GroupDetails?> create() async {
    if (state.name.trim().isEmpty) {
      state = state.copyWith(error: 'Enter a group name');
      return null;
    }
    return ref
        .read(groupRepositoryProvider)
        .createGroup(state.name.trim(), state.selected);
  }
}

final newGroupProvider = NotifierProvider<NewGroupController, NewGroupState>(
  NewGroupController.new,
);
