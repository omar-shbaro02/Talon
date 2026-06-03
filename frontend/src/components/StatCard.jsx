export default function StatCard({ label, value, detail, icon: Icon }) {
  return (
    <section className="panel accent-strip metric-card rounded-lg p-5 pl-6">
      <div className="rainbow-rule mb-4" />
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-slate-500 dark:text-slate-400">{label}</p>
          <div className="mt-2 text-3xl font-black text-slate-950 dark:text-white">{value}</div>
        </div>
        {Icon && (
          <div className="flex size-11 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-900/18">
            <Icon size={20} />
          </div>
        )}
      </div>
      {detail && <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">{detail}</p>}
    </section>
  )
}
