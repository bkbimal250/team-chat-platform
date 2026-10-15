import 'package:flutter/material.dart';

import '../../theme/tokens/gc_colors.dart';
import '../../theme/tokens/gc_radii.dart';

class GcBadge extends StatelessWidget {
  const GcBadge({super.key, required this.count, this.max = 99});

  final int count;
  final int max;

  @override
  Widget build(BuildContext context) {
    if (count <= 0) return const SizedBox.shrink();
    final label = count > max ? '$max+' : '$count';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: GcColors.primary,
        borderRadius: BorderRadius.circular(GcRadii.pill),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
