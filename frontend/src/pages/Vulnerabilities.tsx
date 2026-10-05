// Vulnerabilities — telemetry-sourced findings with CVSS, exploitability and the
// modelled annual loss each one contributes. Filterable by severity/status.

import React, { useMemo, useState } from 'react'
import { ShieldAlert, Bug, Wifi, Wrench } from 'lucide-react'
import { useApi } from '../lib/useApi'
import {
  Loading, ErrorState, CardPad, SectionTitle, Money, Chip, RiskBadge, Disclaimer, StatCard,
} from '../components/ui'
import { num } from '../lib/format'

interface Vuln {
  id: number; cve_id: string; title: string; asset_id: number; asset_name: string
  cvss: number; severity: string; category: string; status: string
  exploit_available: boolean; internet_exposed: boolean; patch_available: boolean
  age_days: number; source: string; ale_inr: number; likelihood: number; sle_inr: number
}
interface VulnResp {
  count: number; by_severity: Record<string, number>; by_status: Record<string, number>; vulnerabilities: Vuln[]
}

const SEVS = ['Critical', 'High', 'Medium', 'Low']

const SubCategoryNode = ({ title, delay, isActive, isExpanded, onClick, children }: {
  title: string; delay: string; isActive: boolean; isExpanded: boolean; onClick: () => void; children: React.ReactNode
}) => {
  return (
    <div className={`relative transition-all duration-[600ms] ease-[cubic-bezier(0.16,1,0.3,1)] ${isActive ? delay : ''}`}>
      {/* Connector Line */}
      <div className="absolute top-1/2 -left-8 w-8 h-px bg-hover/20" />
      
      <button 
        onClick={(e) => {
          e.stopPropagation();
          onClick();
        }}
        className="w-full text-left p-4 rounded-xl bg-elevated/80 backdrop-blur-md border border-hairline shadow-sm hover:shadow-md transition-all"
      >
        <div className="font-medium text-fg">{title}</div>
        
        {/* Expanded Content */}
        <div className={`
          overflow-hidden transition-all duration-[500ms] ease-in-out
          ${isExpanded ? 'max-h-48 mt-3 opacity-100' : 'max-h-0 mt-0 opacity-0'}
        `}>
          {children}
        </div>
      </button>
    </div>
  )
}

export default function Vulnerabilities() {
  const { data, loading, error, reload } = useApi<VulnResp>('/api/vulnerabilities', { refreshOnTelemetry: true })
  const [sev, setSev] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [activeVulnId, setActiveVulnId] = useState<number | null>(null)
  const [expandedSubCategory, setExpandedSubCategory] = useState<string | null>(null)

  const rows = useMemo(() => {
    if (!data) return []
    // Sort by ale_inr desc just to have a good default order like DataTable had
    return data.vulnerabilities
      .filter(v => (!sev || v.severity === sev) && (!status || v.status === status))
      .sort((a, b) => b.ale_inr - a.ale_inr)
  }, [data, sev, status])

  if (loading) return <Loading label="Loading vulnerabilities…" />
  if (error || !data) return <ErrorState message={error ?? 'No data'} onRetry={reload} />

  return (
    <div className="space-y-6">
      <SectionTitle title="Vulnerabilities" subtitle="Correlated from security telemetry, priced by business impact" />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {SEVS.map(s => (
          <button key={s} onClick={() => setSev(sev === s ? null : s)} className={`card card-pad text-left transition ${sev === s ? 'ring-2 ring-brand-500/50' : 'hover:bg-hover/[0.03]'}`}>
            <div className="stat-label">{s}</div>
            <div className="mt-1 text-2xl font-bold text-fg">{num(data.by_severity?.[s] ?? 0)}</div>
          </button>
        ))}
      </div>

      <div 
        className="card card-pad relative"
        onClick={() => {
          setActiveVulnId(null);
          setExpandedSubCategory(null);
        }}
      >
        <SectionTitle title={`${rows.length} of ${data.count} vulnerabilities`} subtitle="Click severity cards to filter"
          right={
            <div className="flex gap-1.5">
              {Object.keys(data.by_status ?? {}).map(st => (
                <button key={st} onClick={() => setStatus(status === st ? null : st)}
                  className={`chip capitalize ${status === st ? 'bg-brand-600/30 text-brand-100 ring-1 ring-brand-500/40' : 'bg-hover/10 text-body'}`}>
                  {st} · {num(data.by_status[st])}
                </button>
              ))}
            </div>
          } />
        
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mt-6">
          {rows.map(v => {
            const isActive = activeVulnId === v.id;
            const isDimmed = activeVulnId !== null && !isActive;

            return (
              <div key={v.id} className={`relative group perspective-1000 ${isActive ? 'z-50' : 'z-10'}`}>
                {/* Node Body */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveVulnId(isActive ? null : v.id);
                    setExpandedSubCategory(null);
                  }}
                  className={`
                    relative z-10 w-full text-left p-5 rounded-2xl bg-elevated border border-hairline
                    transition-all duration-[600ms] ease-[cubic-bezier(0.16,1,0.3,1)]
                    ${isActive ? 'scale-[1.05] shadow-[0_24px_48px_-12px_rgba(0,0,0,0.15)] ring-1 ring-fg/10' : 'hover:bg-hover/[0.03]'}
                    ${isDimmed ? 'opacity-30 blur-[1px] scale-95' : 'opacity-100'}
                  `}
                >
                  <div className="font-semibold text-fg line-clamp-2">{v.title}</div>
                  <div className="flex items-center gap-2 mt-2">
                    <RiskBadge band={v.severity} />
                    <span className="text-sm text-muted">{v.cve_id || '—'}</span>
                  </div>
                  <div className="text-sm text-muted mt-2 truncate">Asset: {v.asset_name}</div>
                  <div className="text-sm text-muted mt-1">CVSS: {v.cvss.toFixed(1)}</div>
                </button>

                {/* Subcategory Branches (Only rendered/visible when active) */}
                <div className={`
                  absolute top-0 right-[-300px] w-64 flex flex-col gap-4 pointer-events-none
                  transition-all duration-[600ms] ease-[cubic-bezier(0.16,1,0.3,1)]
                  ${isActive ? 'opacity-100 translate-x-0 pointer-events-auto' : 'opacity-0 -translate-x-12'}
                `}>
                   {/* Subcategory: Risk Assessment */}
                   <SubCategoryNode 
                     title="Risk Assessment" 
                     delay="delay-[100ms]"
                     isActive={isActive}
                     isExpanded={expandedSubCategory === 'risk'}
                     onClick={() => setExpandedSubCategory(prev => prev === 'risk' ? null : 'risk')}
                   >
                     <div className="text-sm text-body space-y-2">
                       <div className="flex justify-between">
                         <span className="text-muted">Annual Loss (ALE)</span>
                         <Money v={v.ale_inr} className="font-semibold text-risk-high" />
                       </div>
                       <div className="flex justify-between">
                         <span className="text-muted">Single Loss (SLE)</span>
                         <Money v={v.sle_inr} className="font-medium" />
                       </div>
                       <div className="flex justify-between">
                         <span className="text-muted">Likelihood</span>
                         <span className="font-medium">{(v.likelihood * 100).toFixed(1)}%</span>
                       </div>
                     </div>
                   </SubCategoryNode>

                   {/* Subcategory: Details */}
                   <SubCategoryNode 
                     title="Details" 
                     delay="delay-[150ms]"
                     isActive={isActive}
                     isExpanded={expandedSubCategory === 'details'}
                     onClick={() => setExpandedSubCategory(prev => prev === 'details' ? null : 'details')}
                   >
                     <div className="text-sm text-body space-y-1">
                       <div className="flex justify-between">
                         <span className="text-muted">Age</span>
                         <span>{v.age_days} days</span>
                       </div>
                       <div className="flex justify-between">
                         <span className="text-muted">Status</span>
                         <Chip className="bg-hover/10 text-body capitalize">{v.status}</Chip>
                       </div>
                       <div className="flex justify-between">
                         <span className="text-muted">Category</span>
                         <span>{v.category}</span>
                       </div>
                     </div>
                   </SubCategoryNode>

                   {/* Subcategory: Flags */}
                   <SubCategoryNode 
                     title="Flags" 
                     delay="delay-[200ms]"
                     isActive={isActive}
                     isExpanded={expandedSubCategory === 'flags'}
                     onClick={() => setExpandedSubCategory(prev => prev === 'flags' ? null : 'flags')}
                   >
                     <div className="flex flex-wrap gap-2">
                       {v.exploit_available && <span title="Exploit available" className="chip bg-risk-critical/15 text-risk-critical flex items-center gap-1"><Bug className="h-3 w-3" /> Exploit</span>}
                       {v.internet_exposed && <span title="Internet exposed" className="chip bg-risk-high/15 text-risk-high flex items-center gap-1"><Wifi className="h-3 w-3" /> Exposed</span>}
                       {v.patch_available && <span title="Patch available" className="chip bg-risk-low/15 text-risk-low flex items-center gap-1"><Wrench className="h-3 w-3" /> Patch</span>}
                       {!v.exploit_available && !v.internet_exposed && !v.patch_available && (
                         <span className="text-subtle text-sm italic">No special flags</span>
                       )}
                     </div>
                   </SubCategoryNode>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <Disclaimer />
    </div>
  )
}
