import 'package:tflite_v2/tflite_v2.dart';
import 'package:logger/logger.dart';

class TFLiteService {
  final _logger = Logger();
  bool _isModelLoaded = false;

  Future<void> loadModel() async {
    try {
      String? res = await Tflite.loadModel(
        model: "assets/models/modele_cutanee_optimise.tflite",
        labels: "assets/models/labels.txt",
        numThreads: 1, // default
        isAsset: true,
        useGpuDelegate: false, // MobileNetV3Small can be unstable on some mobile GPUs
      );
      _logger.i("Model loaded: $res");
      _isModelLoaded = true;
    } catch (e) {
      _logger.e("Error loading model: $e");
    }
  }

  Future<List?> classifyImage(String imagePath) async {
    if (!_isModelLoaded) {
      _logger.w("Model not loaded yet");
      return null;
    }

    try {
      var recognitions = await Tflite.runModelOnImage(
        path: imagePath,
        imageMean: 0.0,   // Standard MobileNet preprocessing
        imageStd: 255.0,  // normalized to [0,1]
        numResults: 3,    // Top 3 results
        threshold: 0.1,   // Confidence threshold
        asynch: true,
      );
      _logger.i("Recognitions: $recognitions");
      return recognitions;
    } catch (e) {
      _logger.e("Error classifying image: $e");
      return null;
    }
  }

  Future<void> close() async {
    await Tflite.close();
    _isModelLoaded = false;
  }
}
