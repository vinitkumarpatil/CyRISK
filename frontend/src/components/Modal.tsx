// Accessible-ish modal/drawer used for drill-down explainability panels.

import { ReactNode, useEffect } from 'react'
import { X } from 'lucide-react'

export function Modal({ open, onClose, title, children, wide = false }: {
  open: boolean; onClose: () => void; title: ReactNode; children: ReactNode; wide?: boolean
}) {
  useEffect(() => {
    if (!open) return
    const h = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto p-4 sm:p-8">
      <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm" onClick={onClose} />
      <div className={`relative w-full ${wide ? 'max-w-3xl' : 'max-w-xl'} rounded-2xl border border-hairline-strong bg-panel shadow-card`}>
        <div className="flex items-center justify-between border-b border-hairline px-5 py-3.5">
          <h3 className="text-base font-semibold text-fg">{title}</h3>
          <button onClick={onClose} className="rounded-lg p-1 text-muted hover:bg-hover/10 hover:text-fg"><X className="h-5 w-5" /></button>
        </div>
        <div className="max-h-[75vh] overflow-y-auto px-5 py-4">{children}</div>
      </div>
    </div>
  )
}
