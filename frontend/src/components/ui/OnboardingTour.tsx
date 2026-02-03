'use client'

import * as React from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { clsx } from 'clsx'
import { X, ArrowRight, ArrowLeft, Check, Sparkles } from 'lucide-react'

interface TourStep {
  id: string
  title: string
  description: string
  target?: string // CSS selector for element to highlight
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center'
  action?: {
    label: string
    onClick?: () => void
    href?: string
  }
}

interface OnboardingTourProps {
  steps: TourStep[]
  storageKey?: string
  onComplete?: () => void
  onSkip?: () => void
  forceShow?: boolean
}

// Default onboarding steps for ComplianceAgent
export const defaultOnboardingSteps: TourStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to ComplianceAgent! 🎉',
    description: 'Let\'s take a quick tour to help you get started with regulatory compliance monitoring.',
    position: 'center',
  },
  {
    id: 'repositories',
    title: 'Connect Your Repositories',
    description: 'Start by connecting your GitHub repositories. We\'ll scan them for compliance issues automatically.',
    target: '[data-tour="repositories"]',
    position: 'right',
    action: {
      label: 'Connect repository',
      href: '/dashboard/repositories',
    },
  },
  {
    id: 'regulations',
    title: 'Configure Regulations',
    description: 'Choose the regulations that apply to your organization, like GDPR, HIPAA, or SOC 2.',
    target: '[data-tour="regulations"]',
    position: 'right',
    action: {
      label: 'Browse regulations',
      href: '/dashboard/regulations',
    },
  },
  {
    id: 'actions',
    title: 'Review Compliance Actions',
    description: 'When issues are found, you\'ll see actionable items here with suggested fixes.',
    target: '[data-tour="actions"]',
    position: 'right',
  },
  {
    id: 'search',
    title: 'Quick Search & Navigation',
    description: 'Press ⌘K to open the command palette, or use / for quick search from anywhere.',
    target: '[data-search-input]',
    position: 'bottom',
  },
  {
    id: 'complete',
    title: 'You\'re All Set!',
    description: 'Explore the dashboard to see your compliance status at a glance. Happy monitoring!',
    position: 'center',
  },
]

function TourSpotlight({ target }: { target?: string }) {
  const [rect, setRect] = React.useState<DOMRect | null>(null)
  
  React.useEffect(() => {
    if (!target) {
      setRect(null)
      return
    }
    
    const element = document.querySelector(target)
    if (element) {
      setRect(element.getBoundingClientRect())
      
      // Scroll element into view
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [target])
  
  if (!target || !rect) return null
  
  const padding = 8
  
  return (
    <div
      className="absolute rounded-lg ring-4 ring-primary-500 ring-opacity-50 z-40 pointer-events-none transition-all duration-300"
      style={{
        top: rect.top - padding + window.scrollY,
        left: rect.left - padding,
        width: rect.width + padding * 2,
        height: rect.height + padding * 2,
      }}
    />
  )
}

export function OnboardingTour({
  steps,
  storageKey = 'complianceagent-onboarding-complete',
  onComplete,
  onSkip,
  forceShow = false,
}: OnboardingTourProps) {
  const [isOpen, setIsOpen] = React.useState(false)
  const [currentStep, setCurrentStep] = React.useState(0)
  
  // Check if onboarding was completed
  React.useEffect(() => {
    if (forceShow) {
      setIsOpen(true)
      return
    }
    
    const completed = localStorage.getItem(storageKey)
    if (!completed) {
      // Delay showing to let the page render
      const timer = setTimeout(() => setIsOpen(true), 500)
      return () => clearTimeout(timer)
    }
  }, [storageKey, forceShow])
  
  const step = steps[currentStep]
  const isFirstStep = currentStep === 0
  const isLastStep = currentStep === steps.length - 1
  const isCenterPosition = step.position === 'center' || !step.target
  
  const handleNext = () => {
    if (isLastStep) {
      handleComplete()
    } else {
      setCurrentStep((s) => s + 1)
    }
  }
  
  const handlePrev = () => {
    setCurrentStep((s) => Math.max(0, s - 1))
  }
  
  const handleComplete = () => {
    localStorage.setItem(storageKey, 'true')
    setIsOpen(false)
    onComplete?.()
  }
  
  const handleSkip = () => {
    localStorage.setItem(storageKey, 'true')
    setIsOpen(false)
    onSkip?.()
  }
  
  if (!isOpen) return null
  
  return (
    <Dialog.Root open={isOpen} onOpenChange={setIsOpen}>
      <Dialog.Portal>
        {/* Overlay with cutout for target element */}
        <Dialog.Overlay className="fixed inset-0 bg-black/60 z-40" />
        
        {/* Spotlight on target element */}
        <TourSpotlight target={step.target} />
        
        {/* Tour dialog */}
        <Dialog.Content
          className={clsx(
            'fixed z-50 w-full max-w-md bg-white dark:bg-gray-900 rounded-xl shadow-2xl p-6',
            'border border-gray-200 dark:border-gray-700',
            isCenterPosition
              ? 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2'
              : 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 md:top-auto md:bottom-8 md:right-8 md:left-auto md:translate-x-0 md:translate-y-0'
          )}
        >
          {/* Close button */}
          <Dialog.Close className="absolute top-4 right-4 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">
            <X className="h-4 w-4" />
          </Dialog.Close>
          
          {/* Step indicator */}
          <div className="flex items-center gap-1 mb-4">
            {steps.map((_, index) => (
              <div
                key={index}
                className={clsx(
                  'h-1 rounded-full transition-all',
                  index === currentStep
                    ? 'w-6 bg-primary-500'
                    : index < currentStep
                    ? 'w-2 bg-primary-300'
                    : 'w-2 bg-gray-200 dark:bg-gray-700'
                )}
              />
            ))}
          </div>
          
          {/* Content */}
          <div className="mb-6">
            {isCenterPosition && currentStep === 0 && (
              <div className="flex items-center justify-center mb-4">
                <div className="p-3 bg-primary-100 dark:bg-primary-900/30 rounded-full">
                  <Sparkles className="h-8 w-8 text-primary-500" />
                </div>
              </div>
            )}
            <Dialog.Title className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              {step.title}
            </Dialog.Title>
            <Dialog.Description className="text-gray-600 dark:text-gray-400">
              {step.description}
            </Dialog.Description>
          </div>
          
          {/* Action button */}
          {step.action && (
            <div className="mb-6">
              {step.action.href ? (
                <a
                  href={step.action.href}
                  className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 font-medium hover:underline"
                >
                  {step.action.label}
                  <ArrowRight className="h-4 w-4" />
                </a>
              ) : (
                <button
                  onClick={step.action.onClick}
                  className="inline-flex items-center gap-2 text-primary-600 dark:text-primary-400 font-medium hover:underline"
                >
                  {step.action.label}
                  <ArrowRight className="h-4 w-4" />
                </button>
              )}
            </div>
          )}
          
          {/* Navigation */}
          <div className="flex items-center justify-between">
            <button
              onClick={handleSkip}
              className="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              Skip tour
            </button>
            
            <div className="flex items-center gap-2">
              {!isFirstStep && (
                <button
                  onClick={handlePrev}
                  className="flex items-center gap-1 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back
                </button>
              )}
              <button
                onClick={handleNext}
                className="flex items-center gap-1 px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                {isLastStep ? (
                  <>
                    <Check className="h-4 w-4" />
                    Get started
                  </>
                ) : (
                  <>
                    Next
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

// Context to control tour programmatically
interface TourContextValue {
  startTour: () => void
  resetTour: () => void
}

const TourContext = React.createContext<TourContextValue | undefined>(undefined)

export function OnboardingProvider({
  children,
  steps = defaultOnboardingSteps,
  storageKey = 'complianceagent-onboarding-complete',
}: {
  children: React.ReactNode
  steps?: TourStep[]
  storageKey?: string
}) {
  const [forceShow, setForceShow] = React.useState(false)
  
  const startTour = React.useCallback(() => {
    localStorage.removeItem(storageKey)
    setForceShow(true)
  }, [storageKey])
  
  const resetTour = React.useCallback(() => {
    localStorage.removeItem(storageKey)
  }, [storageKey])
  
  return (
    <TourContext.Provider value={{ startTour, resetTour }}>
      {children}
      <OnboardingTour
        steps={steps}
        storageKey={storageKey}
        forceShow={forceShow}
        onComplete={() => setForceShow(false)}
        onSkip={() => setForceShow(false)}
      />
    </TourContext.Provider>
  )
}

export function useTour() {
  const context = React.useContext(TourContext)
  if (!context) {
    throw new Error('useTour must be used within an OnboardingProvider')
  }
  return context
}
