import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import 'widgets/auth_required_view.dart';
import 'widgets/foodai_card.dart';

class FavoritesScreen extends StatelessWidget {
  const FavoritesScreen({
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
        title: 'Favoris verrouillés',
        message:
            'Connecte-toi pour conserver les plats que tu veux retrouver rapidement.',
        onSignInRequested: onSignInRequested,
      );
    }

    return FutureBuilder<List<FavoriteItem>>(
      future: api.getFavorites(),
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(child: Text('Erreur favoris: ${snapshot.error}'));
        }
        final items = snapshot.data ?? [];
        return ListView(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 110),
          children: [
            const FoodAiCard(
              highlightColor: AppTheme.accentSecondary,
              child: _FavoritesHero(),
            ),
            if (items.isEmpty)
              const FoodAiCard(
                highlightColor: AppTheme.accentPrimary,
                child: _FavoritesEmpty(),
              )
            else
              ...items.map((item) => _FavoriteTile(item: item)),
          ],
        );
      },
    );
  }
}

class _FavoritesHero extends StatelessWidget {
  const _FavoritesHero();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
          decoration: BoxDecoration(
            color: AppTheme.accentSecondary.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(999),
          ),
          child: const Text(
            'FAVORITES',
            style: TextStyle(
              color: AppTheme.accentSecondary,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.1,
            ),
          ),
        ),
        const SizedBox(height: 16),
        Text('Tes plats de référence.',
            style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 10),
        const Text(
          'Garde sous la main les résultats que tu veux revoir, comparer ou partager plus tard.',
        ),
      ],
    );
  }
}

class _FavoritesEmpty extends StatelessWidget {
  const _FavoritesEmpty();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        Icon(Icons.favorite_outline_rounded,
            size: 54, color: AppTheme.accentPrimary),
        SizedBox(height: 14),
        Text(
          'Aucun favori pour le moment',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
          textAlign: TextAlign.center,
        ),
        SizedBox(height: 8),
        Text(
          'Ajoute un résultat depuis le site ou une future action mobile pour alimenter cette collection.',
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

class _FavoriteTile extends StatelessWidget {
  const _FavoriteTile({required this.item});

  final FavoriteItem item;

  @override
  Widget build(BuildContext context) {
    return FoodAiCard(
      highlightColor: AppTheme.accentSecondary,
      child: Row(
        children: [
          Container(
            width: 50,
            height: 50,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  AppTheme.accentSecondary.withValues(alpha: 0.95),
                  AppTheme.accentYellow.withValues(alpha: 0.95),
                ],
              ),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(Icons.favorite_rounded, color: AppTheme.bgMain),
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
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: AppTheme.accentPrimary.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    'Confiance ${(item.confidence * 100).toStringAsFixed(1)}%',
                    style: const TextStyle(
                      color: AppTheme.accentPrimary,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
