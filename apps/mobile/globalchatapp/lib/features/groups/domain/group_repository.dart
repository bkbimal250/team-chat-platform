import 'group.dart';

abstract class GroupRepository {
  Future<List<GroupMember>> searchMembers(String query);
  Future<GroupDetails> createGroup(String name, List<GroupMember> members);
  Future<GroupDetails?> getGroup(String groupId);
  Future<void> removeMember(String groupId, String memberId);
  Future<void> leaveGroup(String groupId, String memberId);
}
