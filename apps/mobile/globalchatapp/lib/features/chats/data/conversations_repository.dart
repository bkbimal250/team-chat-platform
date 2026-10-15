import '../../../services/api/conversations/conversations_api.dart';
import '../../../services/api/models/conversation_models.dart';

class ConversationsRepository {
  ConversationsRepository(this._api);

  final ConversationsApi _api;

  Future<List<ConversationDto>> listConversations({
    String? type,
    bool? archived,
  }) =>
      _api.list(type: type, archived: archived);

  Future<ConversationDto> startPersonalDirect(String contactId) =>
      _api.createPersonalDirect(contactId);

  Future<ConversationDto> createPersonalGroup({
    required String title,
    required List<String> memberIds,
  }) =>
      _api.createPersonalGroup(title: title, memberIds: memberIds);

  Future<ConversationDto> createWorkspaceGroup({
    required String title,
    required List<String> memberIds,
  }) =>
      _api.createWorkspaceGroup(title: title, memberIds: memberIds);
}
