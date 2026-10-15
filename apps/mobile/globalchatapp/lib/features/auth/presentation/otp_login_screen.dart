import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../theme/tokens/gc_spacing.dart';
import '../application/auth_controller.dart';
import '../application/auth_state.dart';
import 'widgets/auth_scaffold.dart';

class OtpLoginScreen extends ConsumerStatefulWidget {
  const OtpLoginScreen({super.key});

  @override
  ConsumerState<OtpLoginScreen> createState() => _OtpLoginScreenState();
}

class _OtpLoginScreenState extends ConsumerState<OtpLoginScreen> {
  final _phone = TextEditingController();
  final _code = TextEditingController();
  String? _challengeId;
  String? _devCode;
  var _codeSent = false;

  @override
  void dispose() {
    _phone.dispose();
    _code.dispose();
    super.dispose();
  }

  Future<void> _requestCode() async {
    final phone = _phone.text.trim();
    if (phone.isEmpty) return;
    try {
      final result = await ref.read(authRepositoryProvider).requestOtp(
            phone: phone,
            purpose: 'LOGIN',
          );
      setState(() {
        _challengeId = result.challengeId;
        _devCode = result.developmentCode;
        _codeSent = true;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString())),
      );
    }
  }

  Future<void> _verify() async {
    if (_challengeId == null) return;
    final ok = await ref.read(authControllerProvider.notifier).verifyOtp(
          challengeId: _challengeId!,
          code: _code.text.trim(),
        );
    if (!mounted || !ok) return;
    context.go('/device-setup');
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final loading = auth.status == AuthStatus.authenticating;

    return AuthScaffold(
      title: 'Phone sign-in',
      subtitle: 'We will send a one-time code if your number is eligible.',
      child: Column(
        children: [
          if (auth.errorMessage != null)
            Text(
              auth.errorMessage!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          TextField(
            controller: _phone,
            keyboardType: TextInputType.phone,
            enabled: !_codeSent,
            decoration: const InputDecoration(labelText: 'Phone number'),
          ),
          if (_codeSent) ...[
            const SizedBox(height: GcSpacing.sm),
            TextField(
              controller: _code,
              keyboardType: TextInputType.number,
              maxLength: 6,
              decoration: const InputDecoration(labelText: '6-digit code'),
            ),
            if (_devCode != null)
              Text(
                'Development code: $_devCode',
                style: Theme.of(context).textTheme.bodySmall,
              ),
          ],
          const SizedBox(height: GcSpacing.md),
          FilledButton(
            onPressed: loading
                ? null
                : (_codeSent ? _verify : _requestCode),
            child: Text(_codeSent ? 'Verify and continue' : 'Send code'),
          ),
        ],
      ),
      footer: TextButton(
        onPressed: () => context.pop(),
        child: const Text('Use email instead'),
      ),
    );
  }
}
