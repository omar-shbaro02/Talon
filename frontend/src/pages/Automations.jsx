import { ArrowRight, CheckCircle2, FileText, Mail, Network, UserRoundCog } from 'lucide-react'

const steps = [
  ['Meeting ends', FileText],
  ['Summary generated', CheckCircle2],
  ['Actions extracted', Network],
  ['Client profile updated', UserRoundCog],
  ['Follow-up drafted', Mail],
]

export default function Automations() {
  return (
    <div className="panel rounded-lg p-5">
      <h2 className="text-xl font-black">Workflow Preview</h2>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
        TALON is prepared for Make-style workflow definitions through the automation_workflows table. This preview shows the first coaching automation path.
      </p>
      <div className="mt-8 grid gap-3 lg:grid-cols-5">
        {steps.map(([label, Icon], index) => (
          <div key={label} className="relative rounded-lg border border-slate-200/70 bg-white/70 p-5 dark:border-white/10 dark:bg-white/6">
            <Icon className="text-violet-400" size={26} />
            <div className="mt-4 text-sm font-black">{label}</div>
            {index < steps.length - 1 && <ArrowRight className="absolute -right-5 top-1/2 hidden -translate-y-1/2 text-slate-400 lg:block" size={22} />}
          </div>
        ))}
      </div>
    </div>
  )
}
