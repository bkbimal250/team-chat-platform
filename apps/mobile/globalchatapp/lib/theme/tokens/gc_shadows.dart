import 'package:flutter/material.dart';

abstract final class GcShadows {
  static List<BoxShadow> card(Brightness brightness) => [
        BoxShadow(
          color: brightness == Brightness.light
              ? const Color(0x14172033)
              : const Color(0x40000000),
          blurRadius: 16,
          offset: const Offset(0, 4),
        ),
      ];
}
