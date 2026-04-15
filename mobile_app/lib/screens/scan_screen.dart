import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../models/models.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import 'widgets/foodai_card.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({
    super.key,
    required this.api,
    required this.auth,
    required this.onSignInRequested,
  });

  final ApiService api;
  final AuthService auth;
  final Future<void> Function() onSignInRequested;

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  final _picker = ImagePicker();
  File? _image;
  ScanResponse? _result;
  Recipe? _recipeBase;
  bool _loading = false;
  String? _errorMessage;
  int _servings = 2;
  double _minConfidence = 0.7;

  Future<void> _pick(ImageSource source) async {
    final file = await _picker.pickImage(source: source, imageQuality: 85);
    if (file == null) return;
    setState(() {
      _image = File(file.path);
      _result = null;
      _errorMessage = null;
    });
  }

  Future<void> _scan() async {
    if (_image == null) return;
    setState(() => _loading = true);
    try {
      final data = await widget.api.scanImage(
        _image!,
        servings: _servings,
        minConfidence: _minConfidence,
      );
      setState(() {
        _result = data;
        _recipeBase = data.recipe;
        _errorMessage = null;
      });
    } on DioException catch (error) {
      final detail = error.response?.data is Map<String, dynamic>
          ? (error.response?.data['detail'] as String?)
          : null;
      setState(() {
        _errorMessage =
            detail ?? 'Impossible de contacter le serveur d’analyse.';
      });
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context).textTheme;
    final displayedRecipe = _displayedRecipe;

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 110),
      children: [
        FoodAiCard(
          highlightColor: AppTheme.accentYellow,
          padding: const EdgeInsets.all(22),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                decoration: BoxDecoration(
                  color: AppTheme.accentPrimary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(
                    color: AppTheme.accentPrimary.withValues(alpha: 0.25),
                  ),
                ),
                child: const Text(
                  'MOBILE LAB',
                  style: TextStyle(
                    color: AppTheme.accentPrimary,
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.1,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text('Scanne ton plat en un geste.', style: theme.displaySmall),
              const SizedBox(height: 10),
              const Text(
                'Même univers visuel que le site, avec une analyse plus lisible sur mobile et des réglages accessibles sans friction.',
              ),
              const SizedBox(height: 18),
              const Wrap(
                spacing: 10,
                runSpacing: 10,
                children: [
                  _MetricChip(
                    icon: Icons.flash_on_rounded,
                    label: 'Analyse instantanée',
                  ),
                  _MetricChip(
                    icon: Icons.tune_rounded,
                    label: 'Paramètres ajustables',
                  ),
                  _MetricChip(
                    icon: Icons.auto_awesome_rounded,
                    label: 'Recette suggérée',
                  ),
                ],
              ),
            ],
          ),
        ),
        if (!widget.auth.isLoggedIn)
          FoodAiCard(
            highlightColor: AppTheme.accentSecondary,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 46,
                  height: 46,
                  decoration: BoxDecoration(
                    color: AppTheme.accentSecondary.withValues(alpha: 0.16),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: const Icon(Icons.cloud_sync_rounded,
                      color: AppTheme.accentSecondary),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Synchronise tes scans',
                        style: TextStyle(
                            fontSize: 17, fontWeight: FontWeight.w800),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Connecte-toi avec Google pour retrouver l’historique, les favoris et ton profil sur le site.',
                      ),
                      const SizedBox(height: 14),
                      FilledButton(
                        onPressed: widget.onSignInRequested,
                        child: const Text('Activer la synchro'),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        FoodAiCard(
          highlightColor: AppTheme.accentPrimary,
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const _SectionHeading(
                icon: Icons.camera_alt_rounded,
                title: 'Scan Food Sample',
                subtitle: 'Charge une image ou ouvre la caméra.',
              ),
              const SizedBox(height: 16),
              _ImagePreview(image: _image, loading: _loading),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _pick(ImageSource.camera),
                      icon: const Icon(Icons.camera_alt_outlined),
                      label: const Text('Caméra'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _pick(ImageSource.gallery),
                      icon: const Icon(Icons.photo_library_outlined),
                      label: const Text('Galerie'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 18),
              _ParameterPanel(
                servings: _servings,
                minConfidence: _minConfidence,
                onServingsChanged: (value) {
                  setState(() => _servings = value.round());
                },
                onConfidenceChanged: (value) {
                  setState(() => _minConfidence = value);
                },
              ),
              const SizedBox(height: 18),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: (_loading || _image == null) ? null : _scan,
                  icon: Icon(_loading
                      ? Icons.hourglass_top_rounded
                      : Icons.bolt_rounded),
                  label: Text(
                      _loading ? 'Analyse en cours...' : 'Lancer l’analyse'),
                ),
              ),
            ],
          ),
        ),
        if (_errorMessage != null)
          FoodAiCard(
            highlightColor: AppTheme.warning,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.warning_amber_rounded,
                    color: AppTheme.warning),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    _errorMessage!,
                    style: const TextStyle(color: Colors.white),
                  ),
                ),
              ],
            ),
          ),
        if (_result != null) ...[
          FoodAiCard(
            highlightColor: AppTheme.accentPrimary,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _SectionHeading(
                  icon: Icons.track_changes_rounded,
                  title: 'Neural Predictions',
                  subtitle:
                      'Les meilleures correspondances détectées par le modèle.',
                ),
                if (_result!.warning != null) ...[
                  const SizedBox(height: 14),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppTheme.warning.withValues(alpha: 0.14),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: AppTheme.warning.withValues(alpha: 0.24),
                      ),
                    ),
                    child: Text(
                      _result!.warning!,
                      style: const TextStyle(color: Colors.white),
                    ),
                  ),
                ],
                const SizedBox(height: 14),
                ..._result!.predictions.asMap().entries.map(
                      (entry) => Padding(
                        padding: EdgeInsets.only(
                            bottom: entry.key == _result!.predictions.length - 1
                                ? 0
                                : 12),
                        child: _PredictionTile(
                          rank: entry.key + 1,
                          prediction: entry.value,
                        ),
                      ),
                    ),
              ],
            ),
          ),
          if (displayedRecipe != null)
            FoodAiCard(
              highlightColor: AppTheme.accentYellow,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _SectionHeading(
                    icon: Icons.menu_book_rounded,
                    title: displayedRecipe.name,
                    subtitle: '${displayedRecipe.servings} portions suggérées',
                  ),
                  if (displayedRecipe.ingredients.isNotEmpty) ...[
                    const SizedBox(height: 18),
                    const Text('Ingrédients',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 10),
                    ...displayedRecipe.ingredients.map(
                      (ingredient) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('• ',
                                style: TextStyle(
                                    color: AppTheme.accentPrimary,
                                    fontWeight: FontWeight.bold)),
                            Expanded(
                              child: Text(
                                ingredient.formatted.isEmpty
                                    ? ingredient.display
                                    : '${ingredient.formatted} ${ingredient.display}',
                                style: const TextStyle(color: Colors.white),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                  if (displayedRecipe.steps.isNotEmpty) ...[
                    const SizedBox(height: 18),
                    const Text('Étapes',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 10),
                    ...displayedRecipe.steps.asMap().entries.map(
                          (entry) => Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  width: 26,
                                  height: 26,
                                  alignment: Alignment.center,
                                  decoration: BoxDecoration(
                                    color: AppTheme.accentSecondary
                                        .withValues(alpha: 0.16),
                                    borderRadius: BorderRadius.circular(999),
                                  ),
                                  child: Text(
                                    '${entry.key + 1}',
                                    style: const TextStyle(
                                      color: AppTheme.accentSecondary,
                                      fontWeight: FontWeight.w800,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                    child: Text(entry.value,
                                        style: const TextStyle(
                                            color: Colors.white))),
                              ],
                            ),
                          ),
                        ),
                  ],
                ],
              ),
            ),
        ],
      ],
    );
  }

  Recipe? get _displayedRecipe {
    final baseRecipe = _recipeBase ?? _result?.recipe;
    if (baseRecipe == null) return null;
    if (baseRecipe.servings == _servings) return baseRecipe;

    final ratio = _servings / baseRecipe.servings;
    return Recipe(
      name: baseRecipe.name,
      servings: _servings,
      ingredients: baseRecipe.ingredients
          .map(
            (ingredient) => RecipeIngredient(
              name: ingredient.name,
              display: ingredient.display,
              qty: ingredient.qty == null ? null : ingredient.qty! * ratio,
              unit: ingredient.unit,
              formatted: ingredient.qty == null
                  ? ingredient.formatted
                  : _formatQuantity(ingredient.qty! * ratio, ingredient.unit),
            ),
          )
          .toList(),
      steps: List<String>.from(baseRecipe.steps),
    );
  }

  String _formatQuantity(double qty, String unit) {
    var value = qty;
    var normalizedUnit = unit.toLowerCase();

    if (normalizedUnit == 'g' && value >= 1000) {
      value /= 1000;
      normalizedUnit = 'kg';
    } else if (normalizedUnit == 'ml' && value >= 1000) {
      value /= 1000;
      normalizedUnit = 'l';
    }

    final rounded = (value - value.round()).abs() < 1e-9
        ? '${value.round()}'
        : value.toStringAsFixed(2).replaceFirst(RegExp(r'\.?0+$'), '');

    const labels = {
      'g': ('g', 'g'),
      'kg': ('kg', 'kg'),
      'ml': ('ml', 'ml'),
      'l': ('l', 'l'),
      'tbsp': ('tbsp', 'tbsp'),
      'tsp': ('tsp', 'tsp'),
    };

    if (normalizedUnit == 'piece') {
      return '$rounded ${rounded == '1' ? 'piece' : 'pieces'}';
    }

    final suffix = labels[normalizedUnit];
    return suffix == null ? rounded : '$rounded ${suffix.$1}';
  }
}

class _ImagePreview extends StatelessWidget {
  const _ImagePreview({required this.image, required this.loading});

  final File? image;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 240,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppTheme.border),
        gradient: const LinearGradient(
          colors: [AppTheme.bgCardAlt, AppTheme.bgMainSoft],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(23),
        child: Stack(
          fit: StackFit.expand,
          children: [
            if (image != null)
              Image.file(image!, fit: BoxFit.cover)
            else
              const _EmptyPreview(),
            if (loading)
              ColoredBox(
                color: Colors.black.withValues(alpha: 0.45),
                child: const Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 12),
                      Text('Analyse en cours...',
                          style: TextStyle(color: Colors.white)),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _EmptyPreview extends StatelessWidget {
  const _EmptyPreview();

  @override
  Widget build(BuildContext context) {
    return const Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.image_search_rounded,
            size: 56, color: AppTheme.textSecondary),
        SizedBox(height: 12),
        Text(
          'Aucun sample chargé',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
        ),
        SizedBox(height: 6),
        Text(
          'Prends une photo ou importe une image pour démarrer.',
          textAlign: TextAlign.center,
          style: TextStyle(color: AppTheme.textSecondary),
        ),
      ],
    );
  }
}

class _ParameterPanel extends StatelessWidget {
  const _ParameterPanel({
    required this.servings,
    required this.minConfidence,
    required this.onServingsChanged,
    required this.onConfidenceChanged,
  });

  final int servings;
  final double minConfidence;
  final ValueChanged<double> onServingsChanged;
  final ValueChanged<double> onConfidenceChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('⚙ Parameters',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w800)),
          const SizedBox(height: 14),
          _SliderLabel(
            label: 'Portions',
            value: '$servings',
            color: AppTheme.accentPrimary,
          ),
          Slider(
            value: servings.toDouble(),
            min: 1,
            max: 8,
            divisions: 7,
            activeColor: AppTheme.accentPrimary,
            label: '$servings',
            onChanged: onServingsChanged,
          ),
          _SliderLabel(
            label: 'Seuil de confiance',
            value: minConfidence.toStringAsFixed(2),
            color: AppTheme.accentYellow,
          ),
          Slider(
            value: minConfidence,
            min: 0.1,
            max: 0.95,
            divisions: 17,
            activeColor: AppTheme.accentYellow,
            label: minConfidence.toStringAsFixed(2),
            onChanged: onConfidenceChanged,
          ),
        ],
      ),
    );
  }
}

class _SliderLabel extends StatelessWidget {
  const _SliderLabel({
    required this.label,
    required this.value,
    required this.color,
  });

  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.w700)),
        const Spacer(),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(999),
          ),
          child: Text(
            value,
            style: TextStyle(color: color, fontWeight: FontWeight.w800),
          ),
        ),
      ],
    );
  }
}

class _SectionHeading extends StatelessWidget {
  const _SectionHeading({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(
            color: AppTheme.accentPrimary.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(14),
          ),
          child: Icon(icon, color: AppTheme.accentPrimary),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title,
                  style: const TextStyle(
                      fontSize: 18, fontWeight: FontWeight.w800)),
              const SizedBox(height: 4),
              Text(subtitle,
                  style: const TextStyle(color: AppTheme.textSecondary)),
            ],
          ),
        ),
      ],
    );
  }
}

class _MetricChip extends StatelessWidget {
  const _MetricChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppTheme.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: AppTheme.accentPrimary),
          const SizedBox(width: 8),
          Text(label, style: const TextStyle(fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

class _PredictionTile extends StatelessWidget {
  const _PredictionTile({
    required this.rank,
    required this.prediction,
  });

  final int rank;
  final Prediction prediction;

  @override
  Widget build(BuildContext context) {
    final percent = prediction.confidence * 100;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 30,
                height: 30,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  gradient: rank == 1
                      ? const LinearGradient(colors: [
                          AppTheme.accentPrimary,
                          AppTheme.accentYellow
                        ])
                      : LinearGradient(
                          colors: [
                            AppTheme.accentSecondary.withValues(alpha: 0.8),
                            AppTheme.accentSecondary.withValues(alpha: 0.4),
                          ],
                        ),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Text(
                  '$rank',
                  style: const TextStyle(
                      color: AppTheme.bgMain, fontWeight: FontWeight.w900),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  prediction.label,
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.w800),
                ),
              ),
              Text(
                '${percent.toStringAsFixed(1)}%',
                style: const TextStyle(
                  color: AppTheme.accentPrimary,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(999),
            child: LinearProgressIndicator(
              value: prediction.confidence.clamp(0, 1),
              minHeight: 9,
              backgroundColor: AppTheme.border,
              valueColor:
                  const AlwaysStoppedAnimation<Color>(AppTheme.accentPrimary),
            ),
          ),
        ],
      ),
    );
  }
}
