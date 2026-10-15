import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../theme/tokens/gc_spacing.dart';
import '../application/auth_controller.dart';
import '../application/auth_state.dart';
import 'widgets/auth_scaffold.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  var _obscure = true;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final email = _email.text.trim();
    final password = _password.text;
    if (email.isEmpty || password.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter email and password')),
      );
      return;
    }
    final ok = await ref
        .read(authControllerProvider.notifier)
        .login(email, password);
    if (!mounted || !ok) return;
    context.go('/device-setup');
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final loading = auth.status == AuthStatus.authenticating;

    return AuthScaffold(
      title: 'Sign in',
      subtitle: 'Personal or workspace account — no org required.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (auth.errorMessage != null)
            Padding(
              padding: const EdgeInsets.only(bottom: GcSpacing.sm),
              child: Text(
                auth.errorMessage!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            autofillHints: const [AutofillHints.email],
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(
              labelText: 'Email',
              prefixIcon: Icon(Icons.email_outlined),
            ),
          ),
          const SizedBox(height: GcSpacing.sm),
          TextField(
            controller: _password,
            obscureText: _obscure,
            autofillHints: const [AutofillHints.password],
            onSubmitted: (_) => _submit(),
            decoration: InputDecoration(
              labelText: 'Password',
              prefixIcon: const Icon(Icons.lock_outline),
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
                : const Text('Sign in'),
          ),
          TextButton(
            onPressed: () => context.push('/forgot-password'),
            child: const Text('Forgot password?'),
          ),
          TextButton(
            onPressed: () => context.push('/otp-login'),
            child: const Text('Sign in with phone OTP'),
          ),
        ],
      ),
      footer: TextButton(
        onPressed: () => context.push('/register'),
        child: const Text('Create a personal account'),
      ),
    );
  }
}
