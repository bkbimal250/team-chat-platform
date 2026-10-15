import 'package:flutter/material.dart';

import '../../../components/ui/gc_empty_state.dart';

class UpdatesTabScreen extends StatelessWidget {
  const UpdatesTabScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Updates')),
      body: const GcEmptyState(
        icon: Icons.notifications_none_rounded,
        title: 'No updates yet',
        message:
            'Mentions, reactions, and workspace notifications will show here when connected to GlobalChat.',
      ),
    );
  }
}
