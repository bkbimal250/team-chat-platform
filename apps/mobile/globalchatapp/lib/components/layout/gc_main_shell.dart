import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/navigation/main_tab.dart';

class GcMainShell extends StatelessWidget {
  const GcMainShell({super.key, required this.navigationShell});

  final StatefulNavigationShell navigationShell;

  void _onTap(int index) {
    navigationShell.goBranch(
      index,
      initialLocation: index == navigationShell.currentIndex,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: navigationShell,
      bottomNavigationBar: NavigationBar(
        selectedIndex: navigationShell.currentIndex,
        onDestinationSelected: _onTap,
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.chat_bubble_outline_rounded),
            selectedIcon: const Icon(Icons.chat_bubble_rounded),
            label: MainTab.chats.label,
          ),
          NavigationDestination(
            icon: const Icon(Icons.notifications_none_rounded),
            selectedIcon: const Icon(Icons.notifications_rounded),
            label: MainTab.updates.label,
          ),
          NavigationDestination(
            icon: const Icon(Icons.people_outline_rounded),
            selectedIcon: const Icon(Icons.people_rounded),
            label: MainTab.contacts.label,
          ),
          NavigationDestination(
            icon: const Icon(Icons.apartment_outlined),
            selectedIcon: const Icon(Icons.apartment_rounded),
            label: MainTab.workspace.label,
          ),
          NavigationDestination(
            icon: const Icon(Icons.settings_outlined),
            selectedIcon: const Icon(Icons.settings_rounded),
            label: MainTab.settings.label,
          ),
        ],
      ),
    );
  }
}
