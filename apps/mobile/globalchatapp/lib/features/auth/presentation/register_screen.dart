import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../theme/tokens/gc_spacing.dart';
import '../application/auth_controller.dart';
import '../application/auth_state.dart';
import 'widgets/auth_scaffold.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _password = TextEditingController();
  var _obscure = true;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _phone.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_name.text.trim().length < 2 ||
        _email.text.trim().isEmpty ||
        _phone.text.trim().isEmpty ||
        _password.text.length < 12) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Fill all fields. Password must be at least 12 characters.',
          ),
        ),
      );
      return;
    }
    final ok = await ref.read(authControllerProvider.notifier).registerPersonal(
          displayName: _name.text.trim(),
          email: _email.text.trim(),
          phone: _phone.text.trim(),
          password: _password.text,
        );
    if (!mounted || !ok) return;
    context.go('/device-setup');
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final loading = auth.status == AuthStatus.authenticating;

    return AuthScaffold(
      title: 'Create account',
      subtitle: 'Personal GlobalChat identity (no organization required).',
      child: Column(
        children: [
          if (auth.errorMessage != null)
            Text(
              auth.errorMessage!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          TextField(
            controller: _name,
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(labelText: 'Display name'),
          ),
          const SizedBox(height: GcSpacing.sm),
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'Email'),
          ),
          const SizedBox(height: GcSpacing.sm),
          TextField(
            controller: _phone,
            keyboardType: TextInputType.phone,
            decoration: const InputDecoration(labelText: 'Phone (E.164)'),
          ),
          const SizedBox(height: GcSpacing.sm),
          TextField(
            controller: _password,
            obscureText: _obscure,
            decoration: InputDecoration(
              labelText: 'Password (12+ characters)',
              suffixIcon: IconButton(
                icon: Icon(
                  _obscure ? Icons.visibility_outlined : Icons.visibility_off,
                ),
                onPressed: () => setState(() => _obscure = !_obscure),
              ),
            ),
          ),
          const SizedBox(height: GcSpacing.md),
          FilledButton(
            onPressed: loading ? null : _submit,
            child: loading
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Create account'),
          ),
        ],
      ),
      footer: TextButton(
        onPressed: () => context.go('/login'),
        child: const Text('Already have an account? Sign in'),
      ),
    );
  }
}
