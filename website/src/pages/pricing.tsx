import React, { useState } from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import clsx from 'clsx';
import styles from './pricing.module.css';

type PlanFeature = {
  name: string;
  free: boolean | string;
  pro: boolean | string;
  enterprise: boolean | string;
};

const features: PlanFeature[] = [
  { name: 'Repositories', free: '1', pro: '10', enterprise: 'Unlimited' },
  { name: 'Team members', free: '2', pro: '10', enterprise: 'Unlimited' },
  { name: 'Regulatory frameworks', free: '2', pro: 'All', enterprise: 'All + Custom' },
  { name: 'Compliance scans', free: '10/month', pro: 'Unlimited', enterprise: 'Unlimited' },
  { name: 'AI-powered analysis', free: true, pro: true, enterprise: true },
  { name: 'Code fix generation', free: '5/month', pro: 'Unlimited', enterprise: 'Unlimited' },
  { name: 'PR creation', free: false, pro: true, enterprise: true },
  { name: 'Audit trail', free: '30 days', pro: '1 year', enterprise: 'Unlimited' },
  { name: 'Evidence export', free: false, pro: true, enterprise: true },
  { name: 'API access', free: '60 req/min', pro: '300 req/min', enterprise: 'Unlimited' },
  { name: 'Webhooks', free: false, pro: true, enterprise: true },
  { name: 'CI/CD integration', free: false, pro: true, enterprise: true },
  { name: 'IDE extension', free: true, pro: true, enterprise: true },
  { name: 'Slack/Teams integration', free: false, pro: true, enterprise: true },
  { name: 'SSO/SAML', free: false, pro: false, enterprise: true },
  { name: 'Custom integrations', free: false, pro: false, enterprise: true },
  { name: 'Dedicated support', free: false, pro: false, enterprise: true },
  { name: 'SLA', free: false, pro: '99.9%', enterprise: '99.99%' },
  { name: 'On-premise deployment', free: false, pro: false, enterprise: true },
];

function FeatureCheck({ value }: { value: boolean | string }) {
  if (value === true) {
    return <span className={styles.check}>✓</span>;
  }
  if (value === false) {
    return <span className={styles.dash}>—</span>;
  }
  return <span className={styles.value}>{value}</span>;
}

function PricingCard({
  name,
  price,
  period,
  description,
  features: planFeatures,
  cta,
  ctaLink,
  highlighted = false,
  badge,
}: {
  name: string;
  price: string;
  period?: string;
  description: string;
  features: string[];
  cta: string;
  ctaLink: string;
  highlighted?: boolean;
  badge?: string;
}) {
  return (
    <div className={clsx(styles.pricingCard, highlighted && styles.highlighted)}>
      {badge && <div className={styles.badge}>{badge}</div>}
      <h3 className={styles.planName}>{name}</h3>
      <div className={styles.priceContainer}>
        <span className={styles.price}>{price}</span>
        {period && <span className={styles.period}>/{period}</span>}
      </div>
      <p className={styles.description}>{description}</p>
      <ul className={styles.featureList}>
        {planFeatures.map((feature, i) => (
          <li key={i}>{feature}</li>
        ))}
      </ul>
      <Link
        to={ctaLink}
        className={clsx(
          'button button--lg',
          highlighted ? 'button--primary' : 'button--secondary'
        )}
      >
        {cta}
      </Link>
    </div>
  );
}

function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const faqs = [
    {
      q: 'Can I switch plans later?',
      a: 'Yes! You can upgrade or downgrade at any time. When upgrading, you\'ll get immediate access to new features. When downgrading, the change takes effect at your next billing cycle.',
    },
    {
      q: 'What counts as a "repository"?',
      a: 'A repository is any connected GitHub, GitLab, or Bitbucket repository that ComplianceAgent monitors for compliance. Archived repositories don\'t count toward your limit.',
    },
    {
      q: 'Is there a free trial for Pro?',
      a: 'Yes! All new accounts get a 14-day free trial of Pro features. No credit card required. After the trial, you can continue with Free or upgrade to Pro.',
    },
    {
      q: 'What regulatory frameworks are supported?',
      a: 'We support 15+ frameworks including GDPR, CCPA, HIPAA, SOC 2, ISO 27001, PCI-DSS, EU AI Act, and more. Enterprise customers can request custom framework support.',
    },
    {
      q: 'How does the AI-powered analysis work?',
      a: 'ComplianceAgent uses large language models to parse regulatory text, extract requirements, analyze your code, and generate compliant fixes. All processing happens securely—your code never leaves our infrastructure.',
    },
    {
      q: 'Can I self-host ComplianceAgent?',
      a: 'Yes! Enterprise customers can deploy ComplianceAgent on their own infrastructure (Kubernetes, AWS, GCP, Azure) for complete data control. Contact sales for details.',
    },
    {
      q: 'What support is included?',
      a: 'Free: Community Discord and documentation. Pro: Email support with 24-hour response time. Enterprise: Dedicated success manager, priority support, and custom SLA.',
    },
  ];

  return (
    <div className={styles.faq}>
      <h2>Frequently Asked Questions</h2>
      <div className={styles.faqList}>
        {faqs.map((faq, i) => (
          <div
            key={i}
            className={clsx(styles.faqItem, openIndex === i && styles.open)}
            onClick={() => setOpenIndex(openIndex === i ? null : i)}
          >
            <div className={styles.faqQuestion}>
              {faq.q}
              <span className={styles.faqToggle}>{openIndex === i ? '−' : '+'}</span>
            </div>
            {openIndex === i && <div className={styles.faqAnswer}>{faq.a}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Pricing(): JSX.Element {
  const [annual, setAnnual] = useState(true);

  return (
    <Layout
      title="Pricing"
      description="Simple, transparent pricing for teams of all sizes"
    >
      <main className={styles.pricingPage}>
        {/* Hero */}
        <section className={styles.hero}>
          <h1>Simple, Transparent Pricing</h1>
          <p>Start free, scale as you grow. No hidden fees.</p>
          
          {/* Billing toggle */}
          <div className={styles.billingToggle}>
            <span className={!annual ? styles.active : ''}>Monthly</span>
            <button
              className={styles.toggle}
              onClick={() => setAnnual(!annual)}
              aria-label="Toggle annual billing"
            >
              <span className={clsx(styles.toggleDot, annual && styles.toggleOn)} />
            </button>
            <span className={annual ? styles.active : ''}>
              Annual <span className={styles.discount}>Save 20%</span>
            </span>
          </div>
        </section>

        {/* Pricing cards */}
        <section className={styles.cards}>
          <PricingCard
            name="Free"
            price="$0"
            period="forever"
            description="Perfect for trying out ComplianceAgent on personal projects"
            features={[
              '1 repository',
              '2 team members',
              '2 regulatory frameworks',
              '10 scans per month',
              '5 AI-generated fixes',
              '30-day audit history',
              'Community support',
            ]}
            cta="Get Started Free"
            ctaLink="https://app.complianceagent.io/signup"
          />

          <PricingCard
            name="Pro"
            price={annual ? '$79' : '$99'}
            period="month"
            description="For growing teams that need comprehensive compliance coverage"
            features={[
              '10 repositories',
              '10 team members',
              'All regulatory frameworks',
              'Unlimited scans',
              'Unlimited AI-generated fixes',
              'Auto PR creation',
              '1-year audit history',
              'CI/CD & Slack integration',
              'API access (300 req/min)',
              'Email support',
            ]}
            cta="Start 14-Day Free Trial"
            ctaLink="https://app.complianceagent.io/signup?plan=pro"
            highlighted
            badge="Most Popular"
          />

          <PricingCard
            name="Enterprise"
            price="Custom"
            description="For organizations with advanced security and compliance needs"
            features={[
              'Unlimited repositories',
              'Unlimited team members',
              'Custom frameworks',
              'SSO/SAML authentication',
              'On-premise deployment',
              'Unlimited audit retention',
              'Custom integrations',
              '99.99% SLA',
              'Dedicated success manager',
              'Priority support',
            ]}
            cta="Contact Sales"
            ctaLink="mailto:sales@complianceagent.io"
          />
        </section>

        {/* Feature comparison table */}
        <section className={styles.comparison}>
          <h2>Compare Plans</h2>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>Free</th>
                  <th className={styles.highlightCol}>Pro</th>
                  <th>Enterprise</th>
                </tr>
              </thead>
              <tbody>
                {features.map((feature, i) => (
                  <tr key={i}>
                    <td>{feature.name}</td>
                    <td><FeatureCheck value={feature.free} /></td>
                    <td className={styles.highlightCol}><FeatureCheck value={feature.pro} /></td>
                    <td><FeatureCheck value={feature.enterprise} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Social proof */}
        <section className={styles.socialProof}>
          <h2>Trusted by Engineering Teams</h2>
          <div className={styles.stats}>
            <div className={styles.stat}>
              <span className={styles.statNumber}>500+</span>
              <span className={styles.statLabel}>Organizations</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statNumber}>10,000+</span>
              <span className={styles.statLabel}>Repositories monitored</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statNumber}>1M+</span>
              <span className={styles.statLabel}>Issues detected</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statNumber}>99.9%</span>
              <span className={styles.statLabel}>Uptime</span>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <FAQ />

        {/* CTA */}
        <section className={styles.cta}>
          <h2>Ready to automate compliance?</h2>
          <p>Join 500+ organizations using ComplianceAgent to stay compliant.</p>
          <div className={styles.ctaButtons}>
            <Link
              to="https://app.complianceagent.io/signup"
              className="button button--primary button--lg"
            >
              Start Free Trial
            </Link>
            <Link
              to="/docs"
              className="button button--secondary button--lg"
            >
              View Documentation
            </Link>
          </div>
        </section>
      </main>
    </Layout>
  );
}
