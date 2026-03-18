import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:percent_indicator/percent_indicator.dart';

class ResultScreen extends StatelessWidget {
  final String imagePath;
  final List results;

  const ResultScreen({
    super.key,
    required this.imagePath,
    required this.results,
  });

  @override
  Widget build(BuildContext context) {
    final topResult = results[0];
    final label = topResult['label'].toString().replaceAll('_', ' ');
    final confidence = topResult['confidence'] as double;

    return Scaffold(
      appBar: AppBar(
        title: Text('Analysis Result', style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            Container(
              height: 300,
              width: double.infinity,
              margin: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(24),
                image: DecorationImage(
                  image: FileImage(File(imagePath)),
                  fit: BoxFit.cover,
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Probability',
                              style: GoogleFonts.outfit(color: Colors.grey),
                            ),
                            Text(
                              label,
                              style: GoogleFonts.outfit(
                                fontSize: 28,
                                fontWeight: FontWeight.bold,
                                color: const Color(0xFF1C2431),
                              ),
                            ),
                          ],
                        ),
                      ),
                      CircularPercentIndicator(
                        radius: 40.0,
                        lineWidth: 8.0,
                        percent: confidence,
                        center: Text(
                          "${(confidence * 100).toStringAsFixed(1)}%",
                          style: GoogleFonts.outfit(fontWeight: FontWeight.bold),
                        ),
                        progressColor: _getColor(confidence),
                        backgroundColor: _getColor(confidence).withOpacity(0.1),
                        circularStrokeCap: CircularStrokeCap.round,
                      ),
                    ],
                  ),
                  const SizedBox(height: 30),
                  const Divider(),
                  const SizedBox(height: 20),
                  _buildSectionTitle('What is this?'),
                  const SizedBox(height: 10),
                  Text(
                    _getMockDescription(label),
                    style: GoogleFonts.outfit(fontSize: 16, height: 1.5),
                  ),
                  const SizedBox(height: 30),
                  _buildSectionTitle('Recommendations'),
                  const SizedBox(height: 10),
                  _buildRecommendationCard(
                    Icons.medical_services,
                    'Consult a Professional',
                    'This AI analysis is for information only. Please see a dermatologist.',
                  ),
                  const SizedBox(height: 40),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF2E5BFF),
                        padding: const EdgeInsets.symmetric(vertical: 20),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                      child: Text(
                        'Back to Home',
                        style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getColor(double confidence) {
    if (confidence > 0.7) return Colors.green;
    if (confidence > 0.4) return Colors.orange;
    return Colors.red;
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: GoogleFonts.outfit(
        fontSize: 20,
        fontWeight: FontWeight.bold,
        color: const Color(0xFF1C2431),
      ),
    );
  }

  Widget _buildRecommendationCard(IconData icon, String title, String subtitle) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.red.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.red.withOpacity(0.1)),
      ),
      child: Row(
        children: [
          Icon(icon, color: Colors.red),
          const SizedBox(width: 15),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: GoogleFonts.outfit(fontWeight: FontWeight.bold, color: Colors.red)),
                Text(subtitle, style: GoogleFonts.outfit(fontSize: 12, color: Colors.red.withOpacity(0.8))),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _getMockDescription(String label) {
    label = label.toLowerCase();
    if (label.contains('melanoma')) return 'Melanoma is a serious form of skin cancer. It usually appears as a new mole or a change in an existing mole.';
    if (label.contains('acne')) return 'Acne is a common skin condition where pores become clogged with oil and dead skin cells.';
    if (label.contains('monkeypox')) return 'Monkeypox is a viral zoonosis that can cause a painful rash, enlarged lymph nodes, and fever.';
    return 'Detailed medical information is being updated. Please consult the disease wiki for more details about tropical skin conditions.';
  }
}
