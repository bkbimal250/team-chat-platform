import 'package:flutter/material.dart';

/// GlobalChat brand and semantic colors (light + dark).
abstract final class GcColors {
  static const primary = Color(0xFF635BFF);
  static const primaryDark = Color(0xFF7B74FF);

  static const lightBackground = Color(0xFFF7F8FC);
  static const lightSurface = Color(0xFFFFFFFF);
  static const lightText = Color(0xFF172033);
  static const lightTextSecondary = Color(0xFF5C6478);
  static const lightDivider = Color(0xFFE6E9F2);

  static const darkBackground = Color(0xFF0E1020);
  static const darkSurface = Color(0xFF17192B);
  static const darkText = Color(0xFFF4F5FA);
  static const darkTextSecondary = Color(0xFFA8AEC2);
  static const darkDivider = Color(0xFF2A2D42);

  static const success = Color(0xFF22C55E);
  static const error = Color(0xFFE5484D);
  static const warning = Color(0xFFF5A524);

  static const personalAccent = Color(0xFF635BFF);
  static const workspaceAccent = Color(0xFF0EA5E9);
}
