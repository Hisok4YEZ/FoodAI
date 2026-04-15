import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import 'widgets/auth_required_view.dart';
import 'widgets/foodai_card.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({
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
        title: 'Historique verrouillé',
        message:
            'Connecte-toi pour retrouver tous tes scans et suivre les analyses passées.',
        onSignInRequested: onSignInRequested,
      );
    }

    return FutureBuilder<List<HistoryItem>>(
      future: api.getHistory(),
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text('Erreur historique: ${snapshot.error}'));
        }
        final items = snapshot.data ?? [];
        return ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 110),
          children: [
            const FoodAiCard(
              highlightColor: AppTheme.accentPrimary,
              child: _HistoryHero(),
            ),
            if (items.isEmpty)
              const FoodAiCard(
                highlightColor: AppTheme.accentYellow,
                child: _HistoryEmpty(),
              )
            else
              ...items.map((item) => _HistoryTile(item: item)),
          ],
        );
      },
    );
  }
}

class _HistoryHero extends StatelessWidget {
  const _HistoryHero();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
          decoration: BoxDecoration(
            color: AppTheme.accentPrimary.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(999),
          ),
          child: const Text(
            'SCAN HISTORY',
            style: TextStyle(
              color: AppTheme.accentPrimary,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.1,
            ),
          ),
        ),
        const SizedBox(height: 16),
        Text('Tes derniers passages au labo.',
            style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 10),
        const Text(
          'Chaque entrée conserve la prédiction, la confiance du modèle et le nombre de portions utilisées pendant l’analyse.',
        ),
      ],
    );
  }
}

class _HistoryEmpty extends StatelessWidget {
  const _HistoryEmpty();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        Icon(Icons.history_toggle_off_rounded,
            size: 54, color: AppTheme.accentYellow),
        SizedBox(height: 14),
        Text(
          'Aucun scan enregistré',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
          textAlign: TextAlign.center,
        ),
        SizedBox(height: 8),
        Text(
          'Lance une première analyse depuis l’onglet Scan pour remplir cette timeline.',
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

class _HistoryTile extends StatelessWidget {
  const _HistoryTile({required this.item});

  final HistoryItem item;

  @override
  Widget build(BuildContext context) {
    final date = item.createdAt.split('T').first;

    return FoodAiCard(
      highlightColor: AppTheme.accentSecondary,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 46,
            height: 46,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppTheme.accentPrimary.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(Icons.science_outlined,
                color: AppTheme.accentPrimary),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.predictedDish,
                  style: const TextStyle(
                      fontSize: 17, fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    _MiniStat(
                        label: '${(item.confidence * 100).toStringAsFixed(1)}%',
                        accent: AppTheme.accentPrimary),
                    _MiniStat(
                        label: '${item.servings} portions',
                        accent: AppTheme.accentYellow),
                    _MiniStat(label: date, accent: AppTheme.accentSecondary),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MiniStat extends StatelessWidget {
  const _MiniStat({required this.label, required this.accent});

  final String label;
  final Color accent;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(color: accent, fontWeight: FontWeight.w700),
      ),
    );
  }
}
