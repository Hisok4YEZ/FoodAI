import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import 'widgets/auth_required_view.dart';
import 'widgets/foodai_card.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({
    super.key,
    required this.api,
    required this.auth,
    required this.onSignInRequested,
  });

  final ApiService api;
  final AuthService auth;
  final Future<void> Function() onSignInRequested;

  @override
  Widget build(BuildContext context) {
    if (!auth.isLoggedIn) {
      return AuthRequiredView(
        title: 'Profil verrouillé',
        message:
            'Connecte-toi pour afficher ton identité, tes préférences et ta synchro FoodAI.',
        onSignInRequested: onSignInRequested,
      );
    }

    return FutureBuilder<Map<String, dynamic>>(
      future: api.getProfile(),
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text('Erreur profil: ${snapshot.error}'));
        }
        final p = snapshot.data ?? {};
        final firstName = (p['first_name'] ?? '').toString();
        final lastName = (p['last_name'] ?? '').toString();
        final email = (p['email'] ?? '-').toString();
        final initials =
            '${firstName.isNotEmpty ? firstName[0] : ''}${lastName.isNotEmpty ? lastName[0] : ''}'
                .trim();

        return ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 110),
          children: [
            FoodAiCard(
              highlightColor: AppTheme.accentYellow,
              padding: const EdgeInsets.all(22),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 72,
                        height: 72,
                        alignment: Alignment.center,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: LinearGradient(
                            colors: [
                              AppTheme.accentPrimary,
                              AppTheme.accentYellow
                            ],
                          ),
                        ),
                        child: Text(
                          initials.isEmpty ? 'U' : initials.toUpperCase(),
                          style: const TextStyle(
                            color: AppTheme.bgMain,
                            fontSize: 24,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'PROFILE',
                              style: TextStyle(
                                color: AppTheme.accentYellow,
                                fontSize: 12,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 1.2,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              [firstName, lastName]
                                  .where((value) => value.isNotEmpty)
                                  .join(' ')
                                  .ifEmpty('-'),
                              style: Theme.of(context).textTheme.headlineMedium,
                            ),
                            const SizedBox(height: 4),
                            Text(email),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'Compte synchronisé entre le site FoodAI Lab et cette application mobile.',
                  ),
                ],
              ),
            ),
            FoodAiCard(
              highlightColor: AppTheme.accentPrimary,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Informations',
                      style:
                          TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 14),
                  _ProfileRow(label: 'Email', value: email),
                  _ProfileRow(
                    label: 'Prénom',
                    value: firstName.ifEmpty('-'),
                  ),
                  _ProfileRow(
                    label: 'Nom',
                    value: lastName.ifEmpty('-'),
                  ),
                ],
              ),
            ),
            const FoodAiCard(
              highlightColor: AppTheme.accentSecondary,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Statut',
                      style:
                          TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                  SizedBox(height: 14),
                  _StatusBadge(
                    icon: Icons.verified_user_outlined,
                    label: 'Connexion Google active',
                    accent: AppTheme.accentPrimary,
                  ),
                  SizedBox(height: 10),
                  _StatusBadge(
                    icon: Icons.sync_rounded,
                    label: 'Données prêtes à être partagées avec le site',
                    accent: AppTheme.accentSecondary,
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}

class _ProfileRow extends StatelessWidget {
  const _ProfileRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: const TextStyle(color: AppTheme.textSecondary),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                  color: Colors.white, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({
    required this.icon,
    required this.label,
    required this.accent,
  });

  final IconData icon;
  final String label;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Row(
        children: [
          Icon(icon, color: accent),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              label,
              style: TextStyle(color: accent, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

extension on String {
  String ifEmpty(String fallback) => isEmpty ? fallback : this;
}
