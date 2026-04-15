import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'screens/favorites_screen.dart';
import 'screens/history_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/scan_screen.dart';
import 'services/api_service.dart';
import 'services/auth_service.dart';
import 'theme/app_theme.dart';

final authProvider = Provider<AuthService>((ref) => throw UnimplementedError());
final apiProvider =
    Provider<ApiService>((ref) => ApiService(auth: ref.watch(authProvider)));
final authSessionProvider =
    StreamProvider<Session?>((ref) => ref.watch(authProvider).sessionChanges());

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final auth = await AuthService.create();

  runApp(
    ProviderScope(
      overrides: [authProvider.overrideWithValue(auth)],
      child: const FoodAiMobileApp(),
    ),
  );
}

class FoodAiMobileApp extends ConsumerWidget {
  const FoodAiMobileApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authSession = ref.watch(authSessionProvider);

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'FoodAI Mobile',
      theme: AppTheme.dark(),
      home: authSession.when(
        data: (session) => MainTabs(isLoggedIn: session != null),
        loading: () =>
            const Scaffold(body: Center(child: CircularProgressIndicator())),
        error: (error, stackTrace) => const MainTabs(isLoggedIn: false),
      ),
    );
  }
}

class MainTabs extends ConsumerStatefulWidget {
  const MainTabs({super.key, required this.isLoggedIn});

  final bool isLoggedIn;

  @override
  ConsumerState<MainTabs> createState() => _MainTabsState();
}

class _MainTabsState extends ConsumerState<MainTabs> {
  int _index = 0;
  bool _showLoginPrompt = true;
  bool _authBusy = false;

  Future<void> _signIn() async {
    final auth = ref.read(authProvider);
    if (!auth.isConfigured) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Connexion Google indisponible. Vérifie les variables Supabase dans le backend ou les --dart-define Flutter.',
          ),
        ),
      );
      return;
    }

    setState(() => _authBusy = true);
    try {
      await auth.signInWithGoogle();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Impossible de lancer Google: $error')),
      );
    } finally {
      if (mounted) setState(() => _authBusy = false);
    }
  }

  Future<void> _signOut() async {
    setState(() => _authBusy = true);
    try {
      await ref.read(authProvider).signOut();
      if (mounted) setState(() => _showLoginPrompt = true);
    } finally {
      if (mounted) setState(() => _authBusy = false);
    }
  }

  @override
  void didUpdateWidget(covariant MainTabs oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isLoggedIn && !oldWidget.isLoggedIn) {
      _showLoginPrompt = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final api = ref.watch(apiProvider);
    final pages = [
      ScanScreen(
          api: api, auth: ref.watch(authProvider), onSignInRequested: _signIn),
      HistoryScreen(
          api: api, auth: ref.watch(authProvider), onSignInRequested: _signIn),
      FavoritesScreen(
          api: api, auth: ref.watch(authProvider), onSignInRequested: _signIn),
      ProfileScreen(
          api: api, auth: ref.watch(authProvider), onSignInRequested: _signIn),
    ];

    return DecoratedBox(
      decoration: AppTheme.shellBackground(),
      child: Stack(
        children: [
          ...AppTheme.backgroundOrbs(),
          Scaffold(
            backgroundColor: Colors.transparent,
            extendBody: true,
            appBar: AppBar(
              titleSpacing: 20,
              title: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ShaderMask(
                    shaderCallback: (bounds) =>
                        AppTheme.heroGradient.createShader(bounds),
                    child: const Text(
                      'FoodAI Lab',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w900,
                        color: Colors.white,
                        letterSpacing: -0.8,
                      ),
                    ),
                  ),
                  Text(
                    _tabTagline(_index),
                    style: const TextStyle(
                      fontSize: 11,
                      letterSpacing: 1.3,
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
              actions: [
                Padding(
                  padding: const EdgeInsets.only(right: 12),
                  child: widget.isLoggedIn
                      ? FilledButton.tonalIcon(
                          onPressed: _authBusy ? null : _signOut,
                          icon: const Icon(Icons.logout_rounded),
                          label: const Text('Sortir'),
                        )
                      : OutlinedButton.icon(
                          onPressed: _authBusy ? null : _signIn,
                          icon: const Icon(Icons.login_rounded),
                          label: const Text('Connexion'),
                        ),
                ),
              ],
            ),
            body: Stack(
              children: [
                pages[_index],
                if (!widget.isLoggedIn && _showLoginPrompt)
                  Positioned.fill(
                    child: ColoredBox(
                      color: Colors.black.withValues(alpha: 0.66),
                      child: Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24),
                          child: ConstrainedBox(
                            constraints: const BoxConstraints(maxWidth: 420),
                            child: Container(
                              decoration: BoxDecoration(
                                gradient: AppTheme.panelGradient,
                                borderRadius: BorderRadius.circular(28),
                                border: Border.all(color: AppTheme.border),
                                boxShadow: [
                                  BoxShadow(
                                    color: AppTheme.accentPrimary
                                        .withValues(alpha: 0.14),
                                    blurRadius: 40,
                                    offset: const Offset(0, 18),
                                  ),
                                ],
                              ),
                              child: Padding(
                                padding: const EdgeInsets.all(24),
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  crossAxisAlignment:
                                      CrossAxisAlignment.stretch,
                                  children: [
                                    Container(
                                      width: 72,
                                      height: 72,
                                      decoration: const BoxDecoration(
                                        shape: BoxShape.circle,
                                        gradient: AppTheme.heroGradient,
                                      ),
                                      child: const Icon(Icons.science_rounded,
                                          size: 38, color: AppTheme.bgMain),
                                    ),
                                    const SizedBox(height: 18),
                                    const Text(
                                      'Bienvenue sur FoodAI Lab',
                                      style: TextStyle(
                                          fontSize: 24,
                                          fontWeight: FontWeight.w800),
                                      textAlign: TextAlign.center,
                                    ),
                                    const SizedBox(height: 10),
                                    const Text(
                                      'Connecte-toi pour synchroniser l’historique, les favoris et les préférences entre le site et l’app mobile.',
                                      textAlign: TextAlign.center,
                                    ),
                                    const SizedBox(height: 20),
                                    FilledButton.icon(
                                      onPressed: _authBusy ? null : _signIn,
                                      icon: const Icon(
                                          Icons.account_circle_outlined),
                                      label: Text(_authBusy
                                          ? 'Connexion...'
                                          : 'Continuer avec Google'),
                                    ),
                                    const SizedBox(height: 8),
                                    TextButton(
                                      onPressed: () => setState(
                                          () => _showLoginPrompt = false),
                                      child:
                                          const Text('Continuer sans compte'),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
            bottomNavigationBar: Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(24),
                child: NavigationBar(
                  selectedIndex: _index,
                  onDestinationSelected: (v) => setState(() => _index = v),
                  destinations: const [
                    NavigationDestination(
                        icon: Icon(Icons.camera_alt_outlined),
                        selectedIcon: Icon(Icons.camera_alt_rounded),
                        label: 'Scan'),
                    NavigationDestination(
                        icon: Icon(Icons.history_rounded),
                        selectedIcon: Icon(Icons.history_toggle_off_rounded),
                        label: 'Historique'),
                    NavigationDestination(
                        icon: Icon(Icons.favorite_outline_rounded),
                        selectedIcon: Icon(Icons.favorite_rounded),
                        label: 'Favoris'),
                    NavigationDestination(
                        icon: Icon(Icons.person_outline_rounded),
                        selectedIcon: Icon(Icons.person_rounded),
                        label: 'Profil'),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _tabTagline(int index) {
    switch (index) {
      case 0:
        return 'NEURAL FOOD RECOGNITION';
      case 1:
        return 'SCAN HISTORY';
      case 2:
        return 'FAVORITE DISHES';
      case 3:
        return 'PROFILE & PREFERENCES';
      default:
        return 'FOOD ANALYTICS';
    }
  }
}
