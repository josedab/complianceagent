import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'ComplianceAgent',
  tagline: 'Autonomous Regulatory Monitoring and Adaptation Platform',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://complianceagent.ai',
  baseUrl: '/',

  organizationName: 'josedab',
  projectName: 'complianceagent',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  themes: [
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      {
        hashed: true,
        language: ['en'],
        highlightSearchTermsOnTargetPage: true,
        explicitSearchResultPath: true,
      },
    ],
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/josedab/complianceagent/tree/main/website/',
          showLastUpdateTime: true,
          showLastUpdateAuthor: true,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/complianceagent-social-card.png',
    metadata: [
      {name: 'keywords', content: 'compliance, regulatory, AI, automation, GDPR, CCPA, HIPAA, code generation'},
      {name: 'twitter:card', content: 'summary_large_image'},
    ],
    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    announcementBar: {
      id: 'beta_announcement',
      content: '🚀 ComplianceAgent is in active development. <a target="_blank" rel="noopener noreferrer" href="https://github.com/josedab/complianceagent">Star us on GitHub</a>!',
      backgroundColor: '#0ea5e9',
      textColor: '#ffffff',
      isCloseable: true,
    },
    navbar: {
      title: 'ComplianceAgent',
      logo: {
        alt: 'ComplianceAgent Logo',
        src: 'img/logo.svg',
        srcDark: 'img/logo-dark.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'https://github.com/josedab/complianceagent',
          'aria-label': 'GitHub repository',
          className: 'header-github-link',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {label: 'Getting Started', to: '/docs'},
            {label: 'GitHub', href: 'https://github.com/josedab/complianceagent'},
          ],
        },
        {
          title: 'Community',
          items: [
            {label: 'GitHub Discussions', href: 'https://github.com/josedab/complianceagent/discussions'},
            {label: 'Discord', href: 'https://discord.gg/complianceagent'},
            {label: 'Twitter', href: 'https://twitter.com/complianceagent'},
          ],
        },
        {
          title: 'More',
          items: [
            {label: 'GitHub', href: 'https://github.com/josedab/complianceagent'},
            {label: 'Changelog', href: 'https://github.com/josedab/complianceagent/blob/main/CHANGELOG.md'},
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} ComplianceAgent. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'python', 'typescript', 'json', 'yaml', 'hcl'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
