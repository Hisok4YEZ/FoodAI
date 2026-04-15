import 'package:flutter_test/flutter_test.dart';

import 'package:foodai_mobile/theme/app_theme.dart';

void main() {
  test('dark theme uses FoodAI design tokens', () {
    final theme = AppTheme.dark();

    expect(theme.scaffoldBackgroundColor, AppTheme.bgMain);
    expect(theme.colorScheme.primary, AppTheme.accentPrimary);
    expect(theme.colorScheme.secondary, AppTheme.accentSecondary);
  });
}
