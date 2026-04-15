import 'package:flutter/material.dart';

import '../../theme/app_theme.dart';

class FoodAiCard extends StatelessWidget {
  const FoodAiCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(18),
    this.margin = const EdgeInsets.symmetric(vertical: 8),
    this.highlightColor,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final EdgeInsetsGeometry margin;
  final Color? highlightColor;

  @override
  Widget build(BuildContext context) {
    final glow = highlightColor ?? AppTheme.accentPrimary;

    return Container(
      margin: margin,
      decoration: BoxDecoration(
        gradient: AppTheme.panelGradient,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppTheme.border),
        boxShadow: [
          BoxShadow(
            color: glow.withValues(alpha: 0.08),
            blurRadius: 28,
            offset: const Offset(0, 10),
          ),
          const BoxShadow(
            color: AppTheme.shadow,
            blurRadius: 18,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: Padding(
        padding: padding,
        child: child,
      ),
    );
  }
}
