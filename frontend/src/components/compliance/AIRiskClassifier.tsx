'use client';

import { useState } from 'react';

/**
 * AI Risk classification levels per EU AI Act
 */
export type AIRiskLevel = 'unacceptable' | 'high' | 'limited' | 'minimal';

interface AIRiskClassificationRequest {
  code_content: string;
  file_names: string[];
  system_description: string;
  use_case: string;
  data_types: string[];
}

interface AIRiskClassificationResponse {
  risk_level: AIRiskLevel;
  confidence: number;
  reasons: string[];
  detected_patterns: string[];
  high_risk_areas: string[];
  applicable_requirements: string[];
  recommendations: string[];
}

interface AIRiskClassifierProps {
  onClassificationComplete?: (result: AIRiskClassificationResponse) => void;
  className?: string;
}

const RISK_LEVEL_CONFIG: Record<
  AIRiskLevel,
  { color: string; bgColor: string; label: string; description: string }
> = {
  unacceptable: {
    color: 'text-red-800 dark:text-red-200',
    bgColor: 'bg-red-100 dark:bg-red-900',
    label: 'Unacceptable Risk',
    description: 'This AI system may be prohibited under the EU AI Act',
  },
  high: {
    color: 'text-orange-800 dark:text-orange-200',
    bgColor: 'bg-orange-100 dark:bg-orange-900',
    label: 'High Risk',
    description: 'Subject to strict compliance requirements under EU AI Act',
  },
  limited: {
    color: 'text-yellow-800 dark:text-yellow-200',
    bgColor: 'bg-yellow-100 dark:bg-yellow-900',
    label: 'Limited Risk',
    description: 'Subject to transparency obligations',
  },
  minimal: {
    color: 'text-green-800 dark:text-green-200',
    bgColor: 'bg-green-100 dark:bg-green-900',
    label: 'Minimal Risk',
    description: 'No specific AI Act requirements (general best practices apply)',
  },
};

/**
 * AI Risk Classifier component for analyzing AI systems under EU AI Act
 */
export function AIRiskClassifier({
  onClassificationComplete,
  className = '',
}: AIRiskClassifierProps) {
  const [formData, setFormData] = useState<AIRiskClassificationRequest>({
    code_content: '',
    file_names: [],
    system_description: '',
    use_case: '',
    data_types: [],
  });
  const [fileNamesInput, setFileNamesInput] = useState('');
  const [dataTypesInput, setDataTypesInput] = useState('');
  const [result, setResult] = useState<AIRiskClassificationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    // Parse comma-separated inputs
    const requestData: AIRiskClassificationRequest = {
      ...formData,
      file_names: fileNamesInput
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      data_types: dataTypesInput
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    };

    try {
      const response = await fetch('/api/v1/ai-safety/classify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`Classification failed: ${response.statusText}`);
      }

      const data: AIRiskClassificationResponse = await response.json();
      setResult(data);
      onClassificationComplete?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Classification failed');
    } finally {
      setIsLoading(false);
    }
  };

  const riskConfig = result ? RISK_LEVEL_CONFIG[result.risk_level] : null;

  return (
    <div className={`ai-risk-classifier ${className}`}>
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
          AI System Risk Classification
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Analyze your AI system to determine its risk level under the EU AI Act
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* System Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            System Description
          </label>
          <textarea
            value={formData.system_description}
            onChange={(e) =>
              setFormData({ ...formData, system_description: e.target.value })
            }
            placeholder="Describe what your AI system does..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        {/* Use Case */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Primary Use Case
          </label>
          <input
            type="text"
            value={formData.use_case}
            onChange={(e) => setFormData({ ...formData, use_case: e.target.value })}
            placeholder="e.g., customer support, medical diagnosis, hiring..."
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        {/* Data Types */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Data Types Processed
          </label>
          <input
            type="text"
            value={dataTypesInput}
            onChange={(e) => setDataTypesInput(e.target.value)}
            placeholder="e.g., personal data, biometric, medical (comma-separated)"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        {/* File Names */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Key Files (optional)
          </label>
          <input
            type="text"
            value={fileNamesInput}
            onChange={(e) => setFileNamesInput(e.target.value)}
            placeholder="e.g., model.py, inference.py, train.py (comma-separated)"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          />
        </div>

        {/* Code Content */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Code Sample (optional)
          </label>
          <textarea
            value={formData.code_content}
            onChange={(e) => setFormData({ ...formData, code_content: e.target.value })}
            placeholder="Paste relevant code snippets for analysis..."
            rows={5}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono text-sm"
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-md transition-colors"
        >
          {isLoading ? 'Analyzing...' : 'Classify Risk Level'}
        </button>
      </form>

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Results Display */}
      {result && riskConfig && (
        <div className="mt-6 space-y-4">
          {/* Risk Level Badge */}
          <div
            className={`p-4 rounded-lg ${riskConfig.bgColor} border border-opacity-50`}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className={`text-lg font-bold ${riskConfig.color}`}>
                  {riskConfig.label}
                </h3>
                <p className={`text-sm ${riskConfig.color} opacity-80`}>
                  {riskConfig.description}
                </p>
              </div>
              <div className="text-right">
                <div className={`text-2xl font-bold ${riskConfig.color}`}>
                  {Math.round(result.confidence * 100)}%
                </div>
                <div className={`text-xs ${riskConfig.color} opacity-60`}>
                  Confidence
                </div>
              </div>
            </div>
          </div>

          {/* Detected Patterns */}
          {result.detected_patterns.length > 0 && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                Detected AI/ML Patterns
              </h4>
              <div className="flex flex-wrap gap-2">
                {result.detected_patterns.map((pattern, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded"
                  >
                    {pattern}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* High Risk Areas */}
          {result.high_risk_areas.length > 0 && (
            <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <h4 className="font-medium text-orange-800 dark:text-orange-200 mb-2">
                High-Risk Indicators
              </h4>
              <ul className="list-disc list-inside text-sm text-orange-700 dark:text-orange-300">
                {result.high_risk_areas.map((area, i) => (
                  <li key={i}>{area}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Applicable Requirements */}
          {result.applicable_requirements.length > 0 && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                Applicable Requirements
              </h4>
              <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
                {result.applicable_requirements.map((req, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-blue-500 mt-1">•</span>
                    {req}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <h4 className="font-medium text-green-800 dark:text-green-200 mb-2">
                Recommendations
              </h4>
              <ul className="space-y-1 text-sm text-green-700 dark:text-green-300">
                {result.recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-green-500 mt-1">✓</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
