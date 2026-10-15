import 'package:flutter/material.dart';

import '../../theme/tokens/gc_colors.dart';
import '../../theme/tokens/gc_radii.dart';

enum GcConversationScope { personal, workspace }

class GcScopeChip extends StatelessWidget {
  const GcScopeChip({super.key, required this.scope});

  final GcConversationScope scope;

  @override
  Widget build(BuildContext context) {
    final isPersonal = scope == GcConversationScope.personal;
    final color = isPersonal ? GcColors.personalAccent : GcColors.workspaceAccent;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(GcRadii.pill),
      ),
      child: Text(
        isPersonal ? 'Personal' : 'Workspace',
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }
}
