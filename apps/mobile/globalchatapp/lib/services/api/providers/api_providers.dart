import '../user/user_api.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/session_storage.dart';
import '../auth/auth_api.dart';
import '../client/gateway_client.dart';
import '../contacts/contacts_api.dart';
import '../conversations/conversations_api.dart';
import '../devices/devices_api.dart';
import '../e2ee/e2ee_api.dart';
import '../media/media_api.dart';
import '../messaging/messaging_api.dart';
import '../organization/members_api.dart';

final sessionStorageProvider = Provider((ref) => SessionStorage());

final gatewayClientProvider = Provider(
  (ref) => GatewayClient(sessionStorage: ref.watch(sessionStorageProvider)),
);

final authApiProvider = Provider((ref) => AuthApi(ref.watch(gatewayClientProvider)));
final devicesApiProvider = Provider((ref) => DevicesApi(ref.watch(gatewayClientProvider)));
final e2eeApiProvider = Provider((ref) => E2eeApi(ref.watch(gatewayClientProvider)));
final conversationsApiProvider = Provider(
  (ref) => ConversationsApi(ref.watch(gatewayClientProvider)),
);
final contactsApiProvider = Provider(
  (ref) => ContactsApi(ref.watch(gatewayClientProvider)),
);
final messagingApiProvider = Provider(
  (ref) => MessagingApi(ref.watch(gatewayClientProvider)),
);
final membersApiProvider = Provider(
  (ref) => MembersApi(ref.watch(gatewayClientProvider)),
);
final mediaApiProvider = Provider(
  (ref) => MediaApi(ref.watch(gatewayClientProvider)),
);

final userApiProvider = Provider((ref) => UserApi(ref.watch(gatewayClientProvider)));
