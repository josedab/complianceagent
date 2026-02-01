'use client';

import { useState, useMemo } from 'react';

/**
 * Framework definition type
 */
interface FrameworkDef {
  id: string;
  name: string;
  jurisdiction: string;
}

/**
 * Category definition type
 */
interface CategoryDef {
  name: string;
  description: string;
  icon: string;
  frameworks: FrameworkDef[];
}

/**
 * Framework categories matching the backend source_registry.py
 */
export const FRAMEWORK_CATEGORIES: Record<string, CategoryDef> = {
  privacy_data_protection: {
    name: 'Privacy & Data Protection',
    description: 'Privacy laws and data protection regulations',
    icon: '🔒',
    frameworks: [
      { id: 'gdpr', name: 'GDPR', jurisdiction: 'EU' },
      { id: 'ccpa', name: 'CCPA/CPRA', jurisdiction: 'US-CA' },
      { id: 'hipaa', name: 'HIPAA', jurisdiction: 'US' },
      { id: 'singapore_pdpa', name: 'PDPA', jurisdiction: 'Singapore' },
      { id: 'india_dpdp', name: 'DPDP', jurisdiction: 'India' },
      { id: 'japan_appi', name: 'APPI', jurisdiction: 'Japan' },
      { id: 'korea_pipa', name: 'PIPA', jurisdiction: 'South Korea' },
      { id: 'china_pipl', name: 'PIPL', jurisdiction: 'China' },
    ],
  },
  security_compliance: {
    name: 'Security & Compliance',
    description: 'Security standards and compliance frameworks',
    icon: '🛡️',
    frameworks: [
      { id: 'pci_dss', name: 'PCI-DSS', jurisdiction: 'Global' },
      { id: 'sox', name: 'SOX', jurisdiction: 'US' },
      { id: 'nis2', name: 'NIS2', jurisdiction: 'EU' },
      { id: 'soc2', name: 'SOC 2', jurisdiction: 'Global' },
      { id: 'iso27001', name: 'ISO 27001', jurisdiction: 'Global' },
    ],
  },
  ai_regulation: {
    name: 'AI Regulation',
    description: 'Artificial intelligence governance and safety standards',
    icon: '🤖',
    frameworks: [
      { id: 'eu_ai_act', name: 'EU AI Act', jurisdiction: 'EU' },
      { id: 'nist_ai_rmf', name: 'NIST AI RMF', jurisdiction: 'US' },
      { id: 'iso42001', name: 'ISO 42001', jurisdiction: 'Global' },
    ],
  },
  esg_sustainability: {
    name: 'ESG & Sustainability',
    description: 'Environmental, social, and governance reporting',
    icon: '🌱',
    frameworks: [
      { id: 'csrd', name: 'CSRD', jurisdiction: 'EU' },
      { id: 'sec_climate', name: 'SEC Climate', jurisdiction: 'US' },
      { id: 'tcfd', name: 'TCFD', jurisdiction: 'Global' },
    ],
  },
};

export type FrameworkCategory = keyof typeof FRAMEWORK_CATEGORIES;

interface FrameworkSelectorProps {
  selectedFrameworks: string[];
  onSelectionChange: (frameworks: string[]) => void;
  multiSelect?: boolean;
  showCategories?: boolean;
  filterByRegion?: string;
  className?: string;
}

/**
 * Framework selector component for selecting regulatory frameworks
 * Supports filtering by category (Privacy, Security, AI, ESG) and region
 */
export function FrameworkSelector({
  selectedFrameworks,
  onSelectionChange,
  multiSelect = true,
  showCategories = true,
  filterByRegion,
  className = '',
}: FrameworkSelectorProps) {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(Object.keys(FRAMEWORK_CATEGORIES))
  );

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const toggleFramework = (frameworkId: string) => {
    if (multiSelect) {
      if (selectedFrameworks.includes(frameworkId)) {
        onSelectionChange(selectedFrameworks.filter((id) => id !== frameworkId));
      } else {
        onSelectionChange([...selectedFrameworks, frameworkId]);
      }
    } else {
      onSelectionChange([frameworkId]);
    }
  };

  const filteredCategories = useMemo(() => {
    if (!filterByRegion) return FRAMEWORK_CATEGORIES;

    const filtered: Record<string, CategoryDef> = {};
    for (const [key, category] of Object.entries(FRAMEWORK_CATEGORIES)) {
      const frameworks = category.frameworks.filter(
        (f) =>
          f.jurisdiction.toLowerCase().includes(filterByRegion.toLowerCase()) ||
          f.jurisdiction === 'Global'
      );
      if (frameworks.length > 0) {
        filtered[key] = {
          ...category,
          frameworks: frameworks,
        };
      }
    }
    return filtered;
  }, [filterByRegion]);

  const selectAll = () => {
    const allFrameworks = Object.values(FRAMEWORK_CATEGORIES)
      .flatMap((c) => c.frameworks)
      .map((f) => f.id);
    onSelectionChange(allFrameworks);
  };

  const clearAll = () => {
    onSelectionChange([]);
  };

  return (
    <div className={`framework-selector ${className}`}>
      {/* Header with select/clear buttons */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Regulatory Frameworks
        </h3>
        {multiSelect && (
          <div className="flex gap-2">
            <button
              onClick={selectAll}
              className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400"
            >
              Select All
            </button>
            <span className="text-gray-400">|</span>
            <button
              onClick={clearAll}
              className="text-sm text-gray-600 hover:text-gray-800 dark:text-gray-400"
            >
              Clear
            </button>
          </div>
        )}
      </div>

      {/* Selection summary */}
      <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
        {selectedFrameworks.length} framework{selectedFrameworks.length !== 1 ? 's' : ''} selected
      </div>

      {/* Categories and frameworks */}
      <div className="space-y-4">
        {Object.entries(filteredCategories).map(([categoryKey, category]) => (
          <div
            key={categoryKey}
            className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
          >
            {/* Category header */}
            {showCategories && (
              <button
                onClick={() => toggleCategory(categoryKey)}
                className="w-full flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <span className="text-xl">{category.icon}</span>
                  <div className="text-left">
                    <div className="font-medium text-gray-900 dark:text-white">
                      {category.name}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {category.description}
                    </div>
                  </div>
                </div>
                <span className="text-gray-400">
                  {expandedCategories.has(categoryKey) ? '▼' : '▶'}
                </span>
              </button>
            )}

            {/* Frameworks list */}
            {(!showCategories || expandedCategories.has(categoryKey)) && (
              <div className="p-3 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                {category.frameworks.map((framework) => {
                  const isSelected = selectedFrameworks.includes(framework.id);
                  return (
                    <button
                      key={framework.id}
                      onClick={() => toggleFramework(framework.id)}
                      className={`
                        flex items-center gap-2 p-2 rounded-md text-left text-sm
                        transition-all duration-150
                        ${
                          isSelected
                            ? 'bg-blue-100 dark:bg-blue-900 border-blue-500 text-blue-800 dark:text-blue-200'
                            : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
                        }
                        border
                      `}
                    >
                      <span
                        className={`
                        w-4 h-4 rounded flex-shrink-0 border
                        ${
                          isSelected
                            ? 'bg-blue-500 border-blue-500'
                            : 'border-gray-300 dark:border-gray-600'
                        }
                      `}
                      >
                        {isSelected && (
                          <svg
                            className="w-4 h-4 text-white"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="font-medium truncate">{framework.name}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                          {framework.jurisdiction}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Region filter component for filtering frameworks by geographic region
 */
interface RegionFilterProps {
  selectedRegion: string;
  onRegionChange: (region: string) => void;
  className?: string;
}

const REGIONS = [
  { id: '', name: 'All Regions' },
  { id: 'eu', name: 'Europe' },
  { id: 'us', name: 'United States' },
  { id: 'singapore', name: 'Singapore' },
  { id: 'india', name: 'India' },
  { id: 'japan', name: 'Japan' },
  { id: 'korea', name: 'South Korea' },
  { id: 'china', name: 'China' },
  { id: 'global', name: 'Global' },
];

export function RegionFilter({ selectedRegion, onRegionChange, className = '' }: RegionFilterProps) {
  return (
    <div className={`region-filter ${className}`}>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Filter by Region
      </label>
      <select
        value={selectedRegion}
        onChange={(e) => onRegionChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
      >
        {REGIONS.map((region) => (
          <option key={region.id} value={region.id}>
            {region.name}
          </option>
        ))}
      </select>
    </div>
  );
}
