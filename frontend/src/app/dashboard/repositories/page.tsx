'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { Plus, Search, Code, GitBranch, CheckCircle, RefreshCw, Loader2 } from 'lucide-react'
import { useRepositories, useCreateRepository, useAnalyzeRepository } from '@/hooks/useApi'
import { RepositoriesSkeleton } from '@/components/ui/Skeleton'
import type { Repository } from '@/types'

export default function RepositoriesPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)

  const { data: repositories, loading, error, refetch } = useRepositories()
  const { analyzeRepository, loading: analyzing } = useAnalyzeRepository()

  const filteredRepos = useMemo(() => {
    if (!repositories) return []
    return repositories.filter((repo) =>
      repo.full_name.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }, [repositories, searchQuery])

  const handleAnalyze = async (id: string) => {
    try {
      await analyzeRepository(id)
      refetch()
    } catch (err) {
      console.error('Analysis failed:', err)
    }
  }

  if (loading) {
    return <RepositoriesSkeleton />
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Repositories</h1>
          <p className="text-gray-500">Manage and analyze your code repositories</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="h-5 w-5" />
          Add Repository
        </button>
      </div>

      {error && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 text-sm">
            Unable to load from server. Check your connection.
          </p>
        </div>
      )}

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search repositories..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* Repository Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredRepos.map((repo) => (
          <RepositoryCard 
            key={repo.id} 
            repository={repo} 
            onAnalyze={() => handleAnalyze(repo.id)}
            analyzing={analyzing}
          />
        ))}
      </div>

      {filteredRepos.length === 0 && !loading && (
        <div className="card text-center py-12">
          <Code className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No repositories found</p>
          <button
            onClick={() => setShowAddModal(true)}
            className="mt-4 btn-primary"
          >
            Add Your First Repository
          </button>
        </div>
      )}

      {/* Add Repository Modal */}
      {showAddModal && (
        <AddRepositoryModal 
          onClose={() => setShowAddModal(false)} 
          onSuccess={() => {
            setShowAddModal(false)
            refetch()
          }}
        />
      )}
    </div>
  )
}

function RepositoryCard({ 
  repository, 
  onAnalyze,
  analyzing 
}: { 
  repository: Repository
  onAnalyze: () => void
  analyzing: boolean
}) {
  const isPending = !repository.last_analyzed_at

  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <Link href={`/dashboard/repositories/${repository.id}`} className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 hover:text-primary-600">
            {repository.full_name}
          </h3>
          <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
            <GitBranch className="h-4 w-4" />
            <span>{repository.platform}</span>
            {repository.primary_language && (
              <>
                <span>•</span>
                <span>{repository.primary_language}</span>
              </>
            )}
          </div>
        </Link>
        {isPending ? (
          <button
            onClick={(e) => {
              e.preventDefault()
              onAnalyze()
            }}
            disabled={analyzing}
            className="status-badge status-pending flex items-center gap-1 cursor-pointer hover:bg-gray-200"
          >
            {analyzing ? (
              <>
                <RefreshCw className="h-3 w-3 animate-spin" />
                Analyzing...
              </>
            ) : (
              'Run Analysis'
            )}
          </button>
        ) : (
          <div className="text-3xl font-bold text-green-600">
            —
          </div>
        )}
      </div>

      {!isPending && (
        <>
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">Analysis Status</span>
              <span className="text-gray-900 font-medium">Completed</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all"
                style={{ width: '100%' }}
              />
            </div>
          </div>

          <div className="flex items-center gap-1 text-sm text-green-600">
            <CheckCircle className="h-4 w-4" />
            <span>Analysis complete</span>
          </div>
        </>
      )}

      {repository.last_analyzed_at && (
        <p className="text-xs text-gray-400 mt-4">
          Last analyzed: {new Date(repository.last_analyzed_at).toLocaleDateString()}
        </p>
      )}
    </div>
  )
}

function AddRepositoryModal({ 
  onClose, 
  onSuccess 
}: { 
  onClose: () => void
  onSuccess: () => void 
}) {
  const [platform, setPlatform] = useState<'github' | 'gitlab'>('github')
  const [owner, setOwner] = useState('')
  const [name, setName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const { createRepository } = useCreateRepository()

  const handleSubmit = async () => {
    if (!owner.trim() || !name.trim()) {
      setError('Please enter both owner and repository name')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      await createRepository({
        platform,
        owner: owner.trim(),
        name: name.trim(),
        profile_id: 'default', // Would come from context in real app
      })
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add repository')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Add Repository</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Platform
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button 
                onClick={() => setPlatform('github')}
                className={`flex items-center justify-center gap-2 px-4 py-2 border rounded-lg ${
                  platform === 'github' 
                    ? 'border-primary-500 bg-primary-50 text-primary-700' 
                    : 'border-gray-300 hover:bg-gray-50'
                }`}
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
                GitHub
              </button>
              <button 
                onClick={() => setPlatform('gitlab')}
                className={`flex items-center justify-center gap-2 px-4 py-2 border rounded-lg ${
                  platform === 'gitlab' 
                    ? 'border-primary-500 bg-primary-50 text-primary-700' 
                    : 'border-gray-300 hover:bg-gray-50'
                }`}
              >
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M22.65 14.39L12 22.13 1.35 14.39a.84.84 0 0 1-.3-.94l1.22-3.78 2.44-7.51A.42.42 0 0 1 4.82 2a.43.43 0 0 1 .58 0 .42.42 0 0 1 .11.18l2.44 7.49h8.1l2.44-7.51A.42.42 0 0 1 18.6 2a.43.43 0 0 1 .58 0 .42.42 0 0 1 .11.18l2.44 7.51L23 13.45a.84.84 0 0 1-.35.94z"/>
                </svg>
                GitLab
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Owner / Organization
            </label>
            <input
              type="text"
              placeholder="e.g., acme-corp"
              value={owner}
              onChange={(e) => setOwner(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Repository Name
            </label>
            <input
              type="text"
              placeholder="e.g., backend-api"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button onClick={onClose} className="btn-secondary" disabled={submitting}>
            Cancel
          </button>
          <button 
            onClick={handleSubmit} 
            className="btn-primary flex items-center gap-2"
            disabled={submitting}
          >
            {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
            Add Repository
          </button>
        </div>
      </div>
    </div>
  )
}
