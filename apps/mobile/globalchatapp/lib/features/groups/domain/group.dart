enum GroupRole { owner, admin, member }

class GroupMember {
  const GroupMember(
    this.id,
    this.name, {
    this.role = GroupRole.member,
    this.identityId,
  });
  final String id, name;
  final GroupRole role;
  final String? identityId;
}

class GroupDetails {
  const GroupDetails({
    required this.id,
    required this.name,
    required this.members,
    this.isPersonal = true,
    this.myRole,
  });
  final String id, name;
  final List<GroupMember> members;
  final bool isPersonal;
  final GroupRole? myRole;
}
