import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../services/api/providers/api_providers.dart';
import '../../auth/application/auth_controller.dart';
import '../data/http_group_repository.dart';
import '../domain/group_repository.dart';

final groupRepositoryProvider = Provider<GroupRepository>((ref) {
  final auth = ref.watch(authControllerProvider);
  final user = auth.user;
  return HttpGroupRepository(
    conversations: ref.watch(conversationsApiProvider),
    contacts: ref.watch(contactsApiProvider),
    members: ref.watch(membersApiProvider),
    workspaceActive: user?.organizationId != null,
    currentMemberId: user?.memberId,
    currentIdentityId: user?.identityId,
  );
});
