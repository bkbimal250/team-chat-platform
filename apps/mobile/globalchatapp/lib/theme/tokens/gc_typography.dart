import 'package:flutter/material.dart';

import 'gc_colors.dart';

abstract final class GcTypography {
  static TextTheme textTheme(Brightness brightness) {
    final primary = brightness == Brightness.light
        ? GcColors.lightText
        : GcColors.darkText;
    final secondary = brightness == Brightness.light
        ? GcColors.lightTextSecondary
        : GcColors.darkTextSecondary;
    return TextTheme(
      headlineMedium: TextStyle(
        fontSize: 24,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.2,
        color: primary,
      ),
      titleLarge: TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w600,
        color: primary,
      ),
      titleMedium: TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        color: primary,
      ),
      bodyLarge: TextStyle(fontSize: 16, height: 1.35, color: primary),
      bodyMedium: TextStyle(fontSize: 15, height: 1.35, color: primary),
      bodySmall: TextStyle(fontSize: 13, height: 1.3, color: secondary),
      labelLarge: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        color: primary,
      ),
      labelSmall: TextStyle(fontSize: 12, color: secondary),
    );
  }
}
