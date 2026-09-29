enum GroupRole { owner, admin, member }

class GroupMember {
  const GroupMember(this.id, this.name, {this.role = GroupRole.member});
  final String id, name;
  final GroupRole role;
}

class GroupDetails {
  const GroupDetails({
    required this.id,
    required this.name,
    required this.members,
  });
  final String id, name;
  final List<GroupMember> members;
}
