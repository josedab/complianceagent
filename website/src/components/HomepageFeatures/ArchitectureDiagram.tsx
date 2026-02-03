import React, { useState } from 'react';
import styles from './ArchitectureDiagram.module.css';

interface ComponentInfo {
  id: string;
  title: string;
  description: string;
  color: string;
}

const components: ComponentInfo[] = [
  {
    id: 'monitor',
    title: 'Regulatory Monitor',
    description: 'Continuously monitors 100+ regulatory sources worldwide including EUR-Lex, Federal Register, and national DPAs. Detects changes within hours and provides ML-powered 6-12 month advance warnings.',
    color: '#3b82f6',
  },
  {
    id: 'parser',
    title: 'AI Parser',
    description: 'Transforms legal text into structured requirements using LLMs. Extracts obligations (MUST/SHOULD/MAY), identifies entities, and provides confidence scores with source citations.',
    color: '#8b5cf6',
  },
  {
    id: 'mapper',
    title: 'Codebase Mapper',
    description: 'Analyzes connected repositories to map requirements to code. Uses AST analysis and semantic search to identify affected code and compliance gaps.',
    color: '#06b6d4',
  },
  {
    id: 'generator',
    title: 'Code Generator',
    description: 'Creates context-aware code suggestions and opens pull requests with compliant fixes. Supports Python, TypeScript, Java, Go, and more.',
    color: '#22c55e',
  },
  {
    id: 'audit',
    title: 'Audit Trail',
    description: 'Tamper-proof hash chain records every action. Provides complete evidence trail for auditors with cryptographic verification.',
    color: '#f59e0b',
  },
  {
    id: 'api',
    title: 'REST API',
    description: 'Full-featured API with JWT authentication, rate limiting, and webhooks. Integrates with CI/CD pipelines and external tools.',
    color: '#ec4899',
  },
];

export default function ArchitectureDiagram(): JSX.Element {
  const [activeComponent, setActiveComponent] = useState<ComponentInfo | null>(null);

  return (
    <div className={styles.container}>
      <div className={styles.diagram}>
        {/* External Sources */}
        <div className={styles.section}>
          <div className={styles.sectionLabel}>External Sources</div>
          <div className={styles.externalSources}>
            <div className={styles.sourceBox}>EUR-Lex</div>
            <div className={styles.sourceBox}>Fed Register</div>
            <div className={styles.sourceBox}>DPAs</div>
            <div className={styles.sourceBox}>100+ more</div>
          </div>
        </div>

        {/* Arrow down */}
        <div className={styles.arrow}>↓</div>

        {/* Core Pipeline */}
        <div className={styles.pipeline}>
          <div className={styles.pipelineLabel}>ComplianceAgent Core Pipeline</div>
          <div className={styles.pipelineComponents}>
            {['monitor', 'parser', 'mapper', 'generator'].map((id) => {
              const comp = components.find((c) => c.id === id)!;
              return (
                <div
                  key={id}
                  className={`${styles.component} ${activeComponent?.id === id ? styles.active : ''}`}
                  style={{ '--accent-color': comp.color } as React.CSSProperties}
                  onClick={() => setActiveComponent(activeComponent?.id === id ? null : comp)}
                  onMouseEnter={() => setActiveComponent(comp)}
                  onMouseLeave={() => setActiveComponent(null)}
                >
                  <div className={styles.componentIcon}>
                    {id === 'monitor' && '📡'}
                    {id === 'parser' && '🧠'}
                    {id === 'mapper' && '🗺️'}
                    {id === 'generator' && '⚙️'}
                  </div>
                  <div className={styles.componentTitle}>{comp.title.split(' ')[0]}</div>
                </div>
              );
            })}
          </div>
          <div className={styles.pipelineArrows}>
            <span>→</span>
            <span>→</span>
            <span>→</span>
          </div>
        </div>

        {/* Supporting Services */}
        <div className={styles.services}>
          {['audit', 'api'].map((id) => {
            const comp = components.find((c) => c.id === id)!;
            return (
              <div
                key={id}
                className={`${styles.service} ${activeComponent?.id === id ? styles.active : ''}`}
                style={{ '--accent-color': comp.color } as React.CSSProperties}
                onClick={() => setActiveComponent(activeComponent?.id === id ? null : comp)}
                onMouseEnter={() => setActiveComponent(comp)}
                onMouseLeave={() => setActiveComponent(null)}
              >
                <div className={styles.serviceIcon}>
                  {id === 'audit' && '📋'}
                  {id === 'api' && '🔌'}
                </div>
                <div className={styles.serviceTitle}>{comp.title}</div>
              </div>
            );
          })}
        </div>

        {/* Arrow down */}
        <div className={styles.arrow}>↓</div>

        {/* Your Systems */}
        <div className={styles.section}>
          <div className={styles.sectionLabel}>Your Systems</div>
          <div className={styles.yourSystems}>
            <div className={styles.systemBox}>GitHub Repos</div>
            <div className={styles.systemBox}>CI/CD</div>
            <div className={styles.systemBox}>IDE</div>
          </div>
        </div>
      </div>

      {/* Info Panel */}
      <div className={`${styles.infoPanel} ${activeComponent ? styles.visible : ''}`}>
        {activeComponent && (
          <>
            <h3 style={{ color: activeComponent.color }}>{activeComponent.title}</h3>
            <p>{activeComponent.description}</p>
          </>
        )}
        {!activeComponent && (
          <p className={styles.hint}>Hover over a component to learn more</p>
        )}
      </div>
    </div>
  );
}
