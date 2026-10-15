import 'package:flutter/material.dart';

import '../../theme/tokens/gc_spacing.dart';

class GcAvatar extends StatelessWidget {
  const GcAvatar({
    super.key,
    required this.label,
    this.imageUrl,
    this.size = GcSpacing.listAvatar,
    this.badgeColor,
  });

  final String label;
  final String? imageUrl;
  final double size;
  final Color? badgeColor;

  @override
  Widget build(BuildContext context) {
    final initial = label.isNotEmpty ? label[0].toUpperCase() : '?';
    return Stack(
      clipBehavior: Clip.none,
      children: [
        CircleAvatar(
          radius: size / 2,
          backgroundImage: imageUrl != null ? NetworkImage(imageUrl!) : null,
          child: imageUrl == null ? Text(initial) : null,
        ),
        if (badgeColor != null)
          Positioned(
            right: 0,
            bottom: 0,
            child: Container(
              width: 12,
              height: 12,
              decoration: BoxDecoration(
                color: badgeColor,
                shape: BoxShape.circle,
                border: Border.all(
                  color: Theme.of(context).colorScheme.surface,
                  width: 2,
                ),
              ),
            ),
          ),
      ],
    );
  }
}
