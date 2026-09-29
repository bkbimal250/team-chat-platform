import '../domain/group.dart';
import '../domain/group_repository.dart';

class DemoGroupRepository implements GroupRepository {
  DemoGroupRepository({Iterable<GroupDetails> initialGroups = const []})
    : _groups = {for (final group in initialGroups) group.id: group};
  final Map<String, GroupDetails> _groups;
  static const members = [
    GroupMember('1', 'Alice', role: GroupRole.admin),
    GroupMember('2', 'Bob'),
    GroupMember('3', 'Charlie'),
    GroupMember('4', 'David'),
  ];
  @override
  Future<List<GroupMember>> searchMembers(String query) async => members
      .where((m) => m.name.toLowerCase().contains(query.toLowerCase()))
      .toList();
  @override
  Future<GroupDetails> createGroup(
    String name,
    List<GroupMember> selected,
  ) async =>
      GroupDetails(id: 'demo-${name.hashCode}', name: name, members: selected);
  @override
  Future<GroupDetails?> getGroup(String groupId) async => _groups[groupId];
  @override
  Future<void> removeMember(String groupId, String memberId) async {
    final group = _groups[groupId];
    if (group == null) throw StateError('Group does not exist.');
    _groups[groupId] = GroupDetails(
      id: group.id,
      name: group.name,
      members: group.members.where((m) => m.id != memberId).toList(),
    );
  }

  @override
  Future<void> leaveGroup(String groupId, String memberId) async {
    final group = _groups[groupId];
    if (group == null) {
      throw StateError('Group does not exist.');
    }
    if (!group.members.any((member) => member.id == memberId)) {
      throw StateError('Member does not belong to this group.');
    }
    _groups[groupId] = GroupDetails(
      id: group.id,
      name: group.name,
      members: List.unmodifiable(
        group.members.where((member) => member.id != memberId),
      ),
    );
  }
}
