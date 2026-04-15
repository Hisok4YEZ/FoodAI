import 'dart:io';

import 'package:dio/dio.dart';

import '../core/config.dart';
import '../models/models.dart';
import 'auth_service.dart';

class ApiService {
  ApiService({required AuthService auth})
      : _auth = auth,
        _dio = Dio(BaseOptions(
          baseUrl: AppConfig.baseUrl,
          connectTimeout: const Duration(seconds: 20),
          receiveTimeout: const Duration(seconds: 30),
        ));

  final Dio _dio;
  final AuthService _auth;

  Future<String?> getToken() => _auth.getAccessToken();

  Future<Map<String, String>> _headers() async {
    final token = await getToken();
    if (token == null || token.isEmpty) return {};
    return {'Authorization': 'Bearer $token'};
  }

  Future<ScanResponse> scanImage(
    File image, {
    int servings = 2,
    double minConfidence = 0.7,
  }) async {
    final formData = FormData.fromMap({
      'file': await MultipartFile.fromFile(image.path),
      'servings': servings,
      'min_confidence': minConfidence,
    });
    final res = await _dio.post(
      '/api/scan',
      data: formData,
      options: Options(headers: await _headers()),
    );
    return ScanResponse.fromJson(res.data as Map<String, dynamic>);
  }

  Future<List<HistoryItem>> getHistory() async {
    final token = await getToken();
    if (token == null || token.isEmpty) return [];

    try {
      final res = await _dio.get(
        '/api/history',
        options: Options(headers: await _headers()),
      );
      final data = (res.data as List).cast<Map<String, dynamic>>();
      return data.map(HistoryItem.fromJson).toList();
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 401 || status == 403 || status == 500) return [];
      rethrow;
    }
  }

  Future<List<FavoriteItem>> getFavorites() async {
    final token = await getToken();
    if (token == null || token.isEmpty) return [];

    try {
      final res = await _dio.get(
        '/api/favorites',
        options: Options(headers: await _headers()),
      );
      final data = (res.data as List).cast<Map<String, dynamic>>();
      return data.map(FavoriteItem.fromJson).toList();
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 401 || status == 403 || status == 500) return [];
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getProfile() async {
    final token = await getToken();
    if (token == null || token.isEmpty) {
      return {'guest': true};
    }

    try {
      final res = await _dio.get(
        '/api/profile',
        options: Options(headers: await _headers()),
      );
      return res.data as Map<String, dynamic>;
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 401 || status == 403 || status == 500) {
        return {'guest': true};
      }
      rethrow;
    }
  }
}
