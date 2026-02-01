import Link from 'next/link'
import { Shield, ArrowRight, CheckCircle, AlertTriangle, Code, FileText } from 'lucide-react'

export default function Home() {
  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Shield className="h-8 w-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">ComplianceAgent</span>
          </div>
          <nav className="flex items-center space-x-6">
            <Link href="/dashboard" className="text-gray-600 hover:text-gray-900">
              Dashboard
            </Link>
            <Link href="/login" className="btn-secondary">
              Sign In
            </Link>
            <Link href="/signup" className="btn-primary">
              Get Started
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-b from-primary-50 to-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Autonomous Regulatory Compliance
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            ComplianceAgent automatically monitors regulatory changes, maps them to your code,
            and generates compliant implementations—from GDPR to EU AI Act.
          </p>
          <div className="flex justify-center space-x-4">
            <Link href="/signup" className="btn-primary text-lg px-8 py-3 flex items-center">
              Start Free Trial <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
            <Link href="/demo" className="btn-secondary text-lg px-8 py-3">
              Request Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            End-to-End Compliance Automation
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <FeatureCard
              icon={<AlertTriangle className="h-8 w-8 text-primary-600" />}
              title="Monitor"
              description="Automatically track 100+ regulatory sources across jurisdictions in real-time"
            />
            <FeatureCard
              icon={<FileText className="h-8 w-8 text-primary-600" />}
              title="Parse"
              description="AI extracts actionable requirements from complex legal text"
            />
            <FeatureCard
              icon={<Code className="h-8 w-8 text-primary-600" />}
              title="Map"
              description="Identify exactly which code is affected by each requirement"
            />
            <FeatureCard
              icon={<CheckCircle className="h-8 w-8 text-primary-600" />}
              title="Generate"
              description="Create compliant code modifications with full audit trails"
            />
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="bg-primary-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8 text-center text-white">
            <StatCard value="60%" label="Reduction in Compliance Costs" />
            <StatCard value="2-6 weeks" label="Time to Compliance (vs 6-12 months)" />
            <StatCard value="99%" label="Regulatory Change Detection" />
            <StatCard value="100+" label="Regulations Monitored" />
          </div>
        </div>
      </section>

      {/* Frameworks */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-8">
            Supported Regulatory Frameworks
          </h2>
          <div className="flex flex-wrap justify-center gap-4">
            {['GDPR', 'CCPA/CPRA', 'HIPAA', 'EU AI Act', 'PCI-DSS', 'SOX', 'SOC 2', 'ISO 27001'].map(
              (framework) => (
                <span
                  key={framework}
                  className="px-6 py-3 bg-white rounded-full text-gray-700 font-medium shadow-sm border border-gray-200"
                >
                  {framework}
                </span>
              )
            )}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Ready to Automate Your Compliance?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Start your 14-day free trial. No credit card required.
          </p>
          <Link href="/signup" className="btn-primary text-lg px-8 py-3 inline-flex items-center">
            Get Started Free <ArrowRight className="ml-2 h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Shield className="h-6 w-6 text-white" />
                <span className="text-lg font-bold text-white">ComplianceAgent</span>
              </div>
              <p className="text-sm">
                Autonomous regulatory monitoring and adaptation platform.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/features" className="hover:text-white">Features</Link></li>
                <li><Link href="/pricing" className="hover:text-white">Pricing</Link></li>
                <li><Link href="/integrations" className="hover:text-white">Integrations</Link></li>
                <li><Link href="/docs" className="hover:text-white">Documentation</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/about" className="hover:text-white">About</Link></li>
                <li><Link href="/blog" className="hover:text-white">Blog</Link></li>
                <li><Link href="/careers" className="hover:text-white">Careers</Link></li>
                <li><Link href="/contact" className="hover:text-white">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/privacy" className="hover:text-white">Privacy Policy</Link></li>
                <li><Link href="/terms" className="hover:text-white">Terms of Service</Link></li>
                <li><Link href="/security" className="hover:text-white">Security</Link></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-12 pt-8 text-sm text-center">
            © {new Date().getFullYear()} ComplianceAgent. All rights reserved.
          </div>
        </div>
      </footer>
    </main>
  )
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="card text-center">
      <div className="flex justify-center mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <div>
      <div className="text-4xl font-bold mb-2">{value}</div>
      <div className="text-primary-100">{label}</div>
    </div>
  )
}
