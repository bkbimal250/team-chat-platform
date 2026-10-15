import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/application/auth_controller.dart';

class WorkspaceOrgOption {
  const WorkspaceOrgOption({
    required this.organizationId,
    required this.label,
    required this.memberId,
  });

  final String organizationId;
  final String label;
  final String memberId;
}

class WorkspaceState {
  const WorkspaceState({
    this.loading = false,
    this.organizations = const [],
    this.error,
  });

  final bool loading;
  final List<WorkspaceOrgOption> organizations;
  final String? error;
}

class WorkspaceController extends Notifier<WorkspaceState> {
  @override
  WorkspaceState build() {
    final user = ref.watch(authControllerProvider).user;
    final orgs = <WorkspaceOrgOption>[];
    if (user?.organizationId != null && user?.memberId != null) {
      orgs.add(
        WorkspaceOrgOption(
          organizationId: user!.organizationId!,
          label: 'Current workspace',
          memberId: user.memberId!,
        ),
      );
    }
    return WorkspaceState(organizations: orgs);
  }

  Future<bool> switchToPersonal() async {
    state = WorkspaceState(
      organizations: state.organizations,
      error:
          'Personal context uses your personal login token. Sign in without an organization or use a personal session.',
    );
    return false;
  }

  Future<bool> switchOrganization(String organizationId) async {
    state = WorkspaceState(loading: true, organizations: state.organizations);
    final ok = await ref
        .read(authControllerProvider.notifier)
        .switchOrganization(organizationId);
    state = ok
        ? build()
        : WorkspaceState(
            organizations: state.organizations,
            error: 'Could not switch organization.',
          );
    return ok;
  }
}

final workspaceControllerProvider =
    NotifierProvider<WorkspaceController, WorkspaceState>(
  WorkspaceController.new,
);
