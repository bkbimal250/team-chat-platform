import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'tokens/gc_colors.dart';
import 'tokens/gc_radii.dart';
import 'tokens/gc_typography.dart';

abstract final class GcTheme {
  static ThemeData light() => _build(Brightness.light);
  static ThemeData dark() => _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final isLight = brightness == Brightness.light;
    final scheme = ColorScheme(
      brightness: brightness,
      primary: GcColors.primary,
      onPrimary: Colors.white,
      secondary: isLight ? GcColors.workspaceAccent : GcColors.primaryDark,
      onSecondary: Colors.white,
      error: GcColors.error,
      onError: Colors.white,
      surface: isLight ? GcColors.lightSurface : GcColors.darkSurface,
      onSurface: isLight ? GcColors.lightText : GcColors.darkText,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor:
          isLight ? GcColors.lightBackground : GcColors.darkBackground,
      dividerColor: isLight ? GcColors.lightDivider : GcColors.darkDivider,
      textTheme: GcTypography.textTheme(brightness),
      appBarTheme: AppBarTheme(
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        backgroundColor:
            isLight ? GcColors.lightSurface : GcColors.darkSurface,
        foregroundColor: isLight ? GcColors.lightText : GcColors.darkText,
        systemOverlayStyle: isLight
            ? SystemUiOverlayStyle.dark
            : SystemUiOverlayStyle.light,
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 64,
        backgroundColor:
            isLight ? GcColors.lightSurface : GcColors.darkSurface,
        indicatorColor: GcColors.primary.withValues(alpha: 0.12),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return TextStyle(
            fontSize: 12,
            fontWeight: selected ? FontWeight.w600 : FontWeight.w500,
            color: selected
                ? GcColors.primary
                : (isLight
                    ? GcColors.lightTextSecondary
                    : GcColors.darkTextSecondary),
          );
        }),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: GcColors.primary,
        foregroundColor: Colors.white,
        elevation: 2,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: isLight
            ? GcColors.lightBackground
            : GcColors.darkBackground,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(GcRadii.md),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: isLight ? GcColors.lightSurface : GcColors.darkSurface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(GcRadii.lg),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(GcRadii.sm),
        ),
      ),
    );
  }
}
