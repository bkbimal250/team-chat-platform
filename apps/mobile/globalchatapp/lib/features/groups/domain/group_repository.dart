import 'group.dart';

abstract class GroupRepository {
  Future<List<GroupMember>> searchMembers(String query);
  Future<GroupDetails> createGroup(String name, List<GroupMember> members);
  Future<GroupDetails?> getGroup(String groupId);
  Future<void> addMembers(String groupId, List<String> memberIds);
  Future<void> removeMember(String groupId, String memberId);
  Future<void> leaveGroup(String groupId, String memberId);
  Future<void> deleteGroup(String groupId);
  Future<void> promoteMember(String groupId, String memberId);
  Future<void> demoteMember(String groupId, String memberId);
}
