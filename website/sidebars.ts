import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Getting Started',
      collapsed: false,
      items: [
        'getting-started/installation',
        'getting-started/quick-start',
        'getting-started/configuration',
      ],
    },
    {
      type: 'category',
      label: 'Core Concepts',
      items: [
        'core-concepts/overview',
        'core-concepts/regulatory-monitoring',
        'core-concepts/ai-parsing',
        'core-concepts/codebase-mapping',
        'core-concepts/code-generation',
        'core-concepts/multi-jurisdiction',
      ],
    },
    {
      type: 'category',
      label: 'Guides',
      items: [
        'guides/connecting-repositories',
        'guides/tracking-regulations',
        'guides/generating-compliance-code',
        'guides/cicd-integration',
        'guides/ide-integration',
        'guides/audit-trails',
        'guides/evidence-collection',
      ],
    },
    {
      type: 'category',
      label: 'Frameworks',
      items: [
        'frameworks/overview',
        'frameworks/gdpr',
        'frameworks/ccpa',
        'frameworks/hipaa',
        'frameworks/eu-ai-act',
        'frameworks/pci-dss',
        'frameworks/soc2',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/overview',
        'api/authentication',
        'api/regulations',
        'api/repositories',
        'api/compliance',
        'api/audit',
        'api/billing',
      ],
    },
    {
      type: 'category',
      label: 'Deployment',
      items: [
        'deployment/docker',
        'deployment/aws',
        'deployment/kubernetes',
        'deployment/environment-variables',
      ],
    },
    {
      type: 'category',
      label: 'Troubleshooting',
      items: [
        'troubleshooting/common-issues',
        'troubleshooting/faq',
      ],
    },
    'comparison',
    'contributing',
    'changelog',
  ],
};

export default sidebars;
