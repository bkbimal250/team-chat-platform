import '../../../services/api/contacts/contacts_api.dart';
import '../../../services/api/conversations/conversations_api.dart';
import '../../../services/api/models/contact_models.dart';
import '../../../services/api/organization/members_api.dart';
import '../domain/group.dart';
import '../domain/group_repository.dart';

class HttpGroupRepository implements GroupRepository {
  HttpGroupRepository({
    required ConversationsApi conversations,
    required ContactsApi contacts,
    required MembersApi members,
    required bool workspaceActive,
    required String? currentMemberId,
    required String? currentIdentityId,
  })  : _conversations = conversations,
        _contacts = contacts,
        _members = members,
        _workspaceActive = workspaceActive,
        _currentMemberId = currentMemberId,
        _currentIdentityId = currentIdentityId;

  final ConversationsApi _conversations;
  final ContactsApi _contacts;
  final MembersApi _members;
  final bool _workspaceActive;
  final String? _currentMemberId;
  final String? _currentIdentityId;

  List<ContactDto> _contactsCache = const [];

  GroupRole _mapRole(String role) {
    switch (role) {
      case 'OWNER':
        return GroupRole.owner;
      case 'ADMIN':
        return GroupRole.admin;
      default:
        return GroupRole.member;
    }
  }

  @override
  Future<List<GroupMember>> searchMembers(String query) async {
    final q = query.trim().toLowerCase();
    if (_workspaceActive) {
      final orgMembers = await _members.list();
      return orgMembers
          .where(
            (m) => q.isEmpty || m.displayName.toLowerCase().contains(q),
          )
          .where((m) => m.id != _currentMemberId)
          .map((m) => GroupMember(m.id, m.displayName, identityId: m.userId))
          .toList();
    }
    _contactsCache = await _contacts.list();
    return _contactsCache
        .where((c) => c.contactIdentityId != null)
        .where((c) => q.isEmpty || c.title.toLowerCase().contains(q))
        .map((c) => GroupMember(c.id, c.title))
        .toList();
  }

  @override
  Future<GroupDetails> createGroup(String name, List<GroupMember> members) async {
    final memberIds = members.map((m) => m.id).toList();
    final conversation = _workspaceActive
        ? await _conversations.createWorkspaceGroup(
            title: name,
            memberIds: memberIds,
          )
        : await _conversations.createPersonalGroup(
            title: name,
            memberIds: memberIds,
          );
    return GroupDetails(
      id: conversation.id,
      name: conversation.listTitle,
      members: members,
      isPersonal: conversation.isPersonal,
    );
  }

  @override
  Future<GroupDetails?> getGroup(String groupId) async {
    final conversation = await _conversations.getConversation(groupId);
    if (!conversation.isGroup) return null;
    final rows = await _conversations.listMembers(groupId);
    final contacts = _contactsCache.isEmpty ? await _contacts.list() : _contactsCache;
    final byContactId = {for (final c in contacts) c.contactIdentityId: c};
    final members = rows
        .where((r) => r.status == 'ACTIVE')
        .map((r) {
          final contact = byContactId[r.userId ?? r.memberId];
          final label = contact?.title ?? 'Member';
          return GroupMember(
            conversation.isPersonal ? (contact?.id ?? r.memberId) : r.memberId,
            label,
            role: _mapRole(r.role),
            identityId: r.userId ?? r.memberId,
          );
        })
        .toList();
    GroupRole? myRole;
    final selfKey = _currentMemberId ?? _currentIdentityId;
    if (selfKey != null) {
      for (final r in rows) {
        if (r.memberId == selfKey || r.userId == selfKey) {
          myRole = _mapRole(r.role);
          break;
        }
      }
    }
    return GroupDetails(
      id: conversation.id,
      name: conversation.listTitle,
      members: members,
      isPersonal: conversation.isPersonal,
      myRole: myRole,
    );
  }

  @override
  Future<void> removeMember(String groupId, String memberId) async {
    final conversation = await _conversations.getConversation(groupId);
    final targetId = conversation.isPersonal
        ? (await _resolveIdentityMemberId(groupId, memberId))
        : memberId;
    await _conversations.removeMember(groupId, targetId);
  }

  @override
  Future<void> addMembers(String groupId, List<String> memberIds) async {
    await _conversations.addMembers(groupId, memberIds);
  }

  @override
  Future<void> leaveGroup(String groupId, String memberId) async {
    await _conversations.leaveConversation(groupId);
  }

  @override
  Future<void> deleteGroup(String groupId) async {
    await _conversations.deleteGroup(groupId);
  }

  @override
  Future<void> promoteMember(String groupId, String memberId) async {
    final conversation = await _conversations.getConversation(groupId);
    final target = conversation.isPersonal
        ? await _resolveIdentityMemberId(groupId, memberId)
        : memberId;
    await _conversations.promoteMember(groupId, target);
  }

  @override
  Future<void> demoteMember(String groupId, String memberId) async {
    final conversation = await _conversations.getConversation(groupId);
    final target = conversation.isPersonal
        ? await _resolveIdentityMemberId(groupId, memberId)
        : memberId;
    await _conversations.demoteMember(groupId, target);
  }

  Future<String> _resolveIdentityMemberId(String groupId, String contactId) async {
    final rows = await _conversations.listMembers(groupId);
    final contacts = await _contacts.list();
    final contact = contacts.firstWhere((c) => c.id == contactId);
    final identity = contact.contactIdentityId;
    if (identity == null) throw StateError('Contact is not registered.');
    final row = rows.firstWhere(
      (r) => r.userId == identity || r.memberId == identity,
      orElse: () => throw StateError('Member not in group'),
    );
    return row.memberId;
  }
}
