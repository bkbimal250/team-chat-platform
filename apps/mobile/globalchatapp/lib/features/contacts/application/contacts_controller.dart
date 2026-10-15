import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../services/api/models/contact_models.dart';
import '../../../services/api/providers/api_providers.dart';

class ContactsController extends AsyncNotifier<List<ContactDto>> {
  @override
  Future<List<ContactDto>> build() => ref.watch(contactsApiProvider).list();

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => ref.read(contactsApiProvider).list());
  }
}

final contactsControllerProvider =
    AsyncNotifierProvider<ContactsController, List<ContactDto>>(
  ContactsController.new,
);
