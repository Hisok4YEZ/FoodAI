class Prediction {
  final String label;
  final double confidence;

  Prediction({required this.label, required this.confidence});

  factory Prediction.fromJson(Map<String, dynamic> json) => Prediction(
        label: json['label'] as String,
        confidence: (json['confidence'] as num).toDouble(),
      );
}

class RecipeIngredient {
  final String name;
  final String display;
  final double? qty;
  final String unit;
  final String formatted;

  RecipeIngredient({
    required this.name,
    required this.display,
    required this.qty,
    required this.unit,
    required this.formatted,
  });

  factory RecipeIngredient.fromJson(Map<String, dynamic> json) =>
      RecipeIngredient(
        name: (json['name'] ?? '').toString(),
        display: (json['display'] ?? '').toString(),
        qty: json['qty'] == null ? null : (json['qty'] as num).toDouble(),
        unit: (json['unit'] ?? '').toString(),
        formatted: (json['formatted'] ?? '').toString(),
      );
}

class Recipe {
  final String name;
  final int servings;
  final List<RecipeIngredient> ingredients;
  final List<String> steps;

  Recipe({
    required this.name,
    required this.servings,
    required this.ingredients,
    required this.steps,
  });

  factory Recipe.fromJson(Map<String, dynamic> json) => Recipe(
        name: json['name'] as String,
        servings: json['servings'] as int,
        ingredients: ((json['ingredients'] as List?) ?? const [])
            .map((e) => RecipeIngredient.fromJson(e as Map<String, dynamic>))
            .toList(),
        steps: ((json['steps'] as List?) ?? const [])
            .map((e) => e.toString())
            .toList(),
      );
}

class ScanResponse {
  final List<Prediction> predictions;
  final Recipe? recipe;
  final String? warning;

  ScanResponse({required this.predictions, this.recipe, this.warning});

  factory ScanResponse.fromJson(Map<String, dynamic> json) => ScanResponse(
        predictions: ((json['predictions'] as List?) ?? const [])
            .map((e) => Prediction.fromJson(e as Map<String, dynamic>))
            .toList(),
        recipe: json['recipe'] == null
            ? null
            : Recipe.fromJson(json['recipe'] as Map<String, dynamic>),
        warning: json['warning'] as String?,
      );
}

class HistoryItem {
  final String id;
  final String predictedDish;
  final double confidence;
  final int servings;
  final String createdAt;

  HistoryItem({
    required this.id,
    required this.predictedDish,
    required this.confidence,
    required this.servings,
    required this.createdAt,
  });

  factory HistoryItem.fromJson(Map<String, dynamic> json) => HistoryItem(
        id: json['id'] as String,
        predictedDish: json['predicted_dish'] as String,
        confidence: (json['confidence'] as num).toDouble(),
        servings: json['servings'] as int,
        createdAt: json['created_at'] as String,
      );
}

class FavoriteItem {
  final String id;
  final String predictedDish;
  final double confidence;

  FavoriteItem({
    required this.id,
    required this.predictedDish,
    required this.confidence,
  });

  factory FavoriteItem.fromJson(Map<String, dynamic> json) => FavoriteItem(
        id: json['id'] as String,
        predictedDish: json['predicted_dish'] as String,
        confidence: (json['confidence'] as num).toDouble(),
      );
}
