// Generic, lightweight data table with typed column defs. Sorting is optional
// and client-side; rendering is delegated to each column's render fn.

import { ReactNode, useMemo, useState } from 'react'
import { ArrowDown, ArrowUp } from 'lucide-react'
import { EmptyState } from './ui'

export interface Column<T> {
  key: string
  header: ReactNode
  render: (row: T) => ReactNode
  /** Value used for client-side sorting; omit to make the column unsortable. */
  sortValue?: (row: T) => number | string
  className?: string
  align?: 'left' | 'right' | 'center'
}

export function DataTable<T>({
  columns, rows, empty = 'No data', initialSort, dense = false, onRowClick,
}: {
  columns: Column<T>[]
  rows: T[]
  empty?: string
  initialSort?: { key: string; dir: 'asc' | 'desc' }
  dense?: boolean
  onRowClick?: (row: T) => void
}) {
  const [sort, setSort] = useState(initialSort)

  const sorted = useMemo(() => {
    if (!sort) return rows
    const col = columns.find(c => c.key === sort.key)
    if (!col?.sortValue) return rows
    const dir = sort.dir === 'asc' ? 1 : -1
    return [...rows].sort((a, b) => {
      const av = col.sortValue!(a), bv = col.sortValue!(b)
      if (av < bv) return -1 * dir
      if (av > bv) return 1 * dir
      return 0
    })
  }, [rows, sort, columns])

  function toggle(key: string) {
    const col = columns.find(c => c.key === key)
    if (!col?.sortValue) return
    setSort(s => s && s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'desc' })
  }

  if (!rows.length) return <EmptyState message={empty} />

  const pad = dense ? 'px-3 py-1.5' : 'px-3 py-2.5'
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-hairline-strong text-left text-xs uppercase tracking-wider text-muted">
            {columns.map(c => (
              <th
                key={c.key}
                className={`${pad} font-medium ${c.align === 'right' ? 'text-right' : c.align === 'center' ? 'text-center' : ''} ${c.sortValue ? 'cursor-pointer select-none hover:text-fg' : ''}`}
                onClick={() => toggle(c.key)}
              >
                <span className="inline-flex items-center gap-1">
                  {c.header}
                  {sort?.key === c.key && (sort.dir === 'asc' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr
              key={i}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={`border-b border-hairline text-body last:border-0 hover:bg-hover/[0.04] ${onRowClick ? 'cursor-pointer' : ''}`}
            >
              {columns.map(c => (
                <td key={c.key} className={`${pad} ${c.align === 'right' ? 'text-right tabular-nums' : c.align === 'center' ? 'text-center' : ''} ${c.className ?? ''}`}>
                  {c.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
