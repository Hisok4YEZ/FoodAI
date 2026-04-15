import 'package:flutter/material.dart';

import '../../theme/app_theme.dart';
import 'foodai_card.dart';

class AuthRequiredView extends StatelessWidget {
  const AuthRequiredView({
    super.key,
    required this.title,
    required this.message,
    required this.onSignInRequested,
  });

  final String title;
  final String message;
  final Future<void> Function() onSignInRequested;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Center(
        child: FoodAiCard(
          highlightColor: AppTheme.accentSecondary,
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 68,
                height: 68,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(
                    colors: [
                      AppTheme.accentSecondary.withValues(alpha: 0.9),
                      AppTheme.accentYellow.withValues(alpha: 0.9),
                    ],
                  ),
                ),
                child: const Icon(Icons.lock_open_rounded,
                    size: 34, color: AppTheme.bgMain),
              ),
              const SizedBox(height: 18),
              Text(
                title,
                style: Theme.of(context).textTheme.headlineMedium,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 10),
              Text(message, textAlign: TextAlign.center),
              const SizedBox(height: 22),
              FilledButton.icon(
                onPressed: onSignInRequested,
                icon: const Icon(Icons.login),
                label: const Text('Continuer avec Google'),
              ),
              const SizedBox(height: 10),
              const Text(
                'Historique, favoris et profil restent synchronisés une fois connecté.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppTheme.textSecondary),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
