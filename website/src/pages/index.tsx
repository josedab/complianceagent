import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <p style={{fontSize: '1.25rem', opacity: 0.9, maxWidth: '700px', margin: '0 auto 2rem'}}>
          Monitor 100+ regulatory frameworks, automatically map requirements to your codebase, 
          and generate compliant code modifications—all powered by AI.
        </p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs">
            Get Started →
          </Link>
          <Link
            className="button button--outline button--secondary button--lg"
            style={{marginLeft: '1rem'}}
            href="https://github.com/josedab/complianceagent">
            GitHub ★
          </Link>
        </div>
      </div>
    </header>
  );
}

type FeatureItem = {
  title: string;
  icon: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Regulatory Monitoring',
    icon: '🔍',
    description: (
      <>
        Continuously track 100+ regulatory sources including GDPR, CCPA, HIPAA, 
        EU AI Act, and more. Get instant alerts when regulations change.
      </>
    ),
  },
  {
    title: 'AI-Powered Parsing',
    icon: '🤖',
    description: (
      <>
        Extract actionable requirements from legal text using GitHub Copilot SDK. 
        Understand obligations with confidence scoring and citations.
      </>
    ),
  },
  {
    title: 'Codebase Mapping',
    icon: '🗺️',
    description: (
      <>
        Automatically identify which code is affected by each requirement. 
        See exactly where compliance gaps exist in your repositories.
      </>
    ),
  },
  {
    title: 'Code Generation',
    icon: '⚡',
    description: (
      <>
        Generate compliant code modifications with full audit trails. 
        Create PRs automatically with context and documentation.
      </>
    ),
  },
  {
    title: 'Multi-Jurisdiction',
    icon: '🌍',
    description: (
      <>
        Handle conflicting requirements across regions with configurable 
        resolution strategies. Support for APAC, EU, and US regulations.
      </>
    ),
  },
  {
    title: 'Enterprise Ready',
    icon: '🏢',
    description: (
      <>
        SSO/SAML authentication, SCIM provisioning, tamper-proof audit trails, 
        and multi-tenant architecture for enterprise deployments.
      </>
    ),
  },
];

function Feature({title, icon, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center" style={{fontSize: '3rem', marginBottom: '1rem'}}>
        {icon}
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}

function FrameworksSection(): ReactNode {
  const frameworks = [
    {name: 'GDPR', region: 'EU'},
    {name: 'CCPA', region: 'US-CA'},
    {name: 'HIPAA', region: 'US'},
    {name: 'EU AI Act', region: 'EU'},
    {name: 'PCI-DSS', region: 'Global'},
    {name: 'SOC 2', region: 'Global'},
    {name: 'ISO 27001', region: 'Global'},
    {name: 'PDPA', region: 'Singapore'},
  ];

  return (
    <section style={{padding: '4rem 0', background: 'var(--ifm-background-surface-color)'}}>
      <div className="container">
        <div className="text--center" style={{marginBottom: '2rem'}}>
          <Heading as="h2">100+ Supported Frameworks</Heading>
          <p>From privacy regulations to AI safety standards</p>
        </div>
        <div className="row" style={{justifyContent: 'center'}}>
          {frameworks.map((fw, idx) => (
            <div key={idx} className="col col--2" style={{textAlign: 'center', margin: '0.5rem'}}>
              <div style={{
                padding: '1rem',
                borderRadius: '0.5rem',
                background: 'var(--ifm-background-color)',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}>
                <strong>{fw.name}</strong>
                <div style={{fontSize: '0.75rem', opacity: 0.7}}>{fw.region}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function QuickStartSection(): ReactNode {
  return (
    <section style={{padding: '4rem 0'}}>
      <div className="container">
        <div className="row">
          <div className="col col--6">
            <Heading as="h2">Up and Running in Minutes</Heading>
            <p>
              ComplianceAgent runs entirely in Docker. Clone the repo, start the containers, 
              and access your compliance dashboard immediately.
            </p>
            <Link className="button button--primary button--lg" to="/docs">
              Read the Docs →
            </Link>
          </div>
          <div className="col col--6">
            <pre style={{
              background: '#1e293b',
              color: '#e2e8f0',
              padding: '1.5rem',
              borderRadius: '0.5rem',
              fontSize: '0.9rem',
              overflow: 'auto',
            }}>
{`# Clone and start
git clone https://github.com/josedab/complianceagent.git
cd complianceagent

# Configure and launch
cp .env.example .env
cd docker && docker-compose up -d

# Access the dashboard
open http://localhost:3000`}
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="AI-Powered Compliance Automation"
      description="ComplianceAgent - Autonomous regulatory monitoring and adaptation platform. Monitor regulations, map to code, generate compliance fixes.">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        <FrameworksSection />
        <QuickStartSection />
      </main>
    </Layout>
  );
}
