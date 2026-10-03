import React, { useState, useMemo } from 'react';
import { FEATURES } from '../features';

export const FeatureCatalogTable: React.FC = () => {
  const [filterQuery, setFilterQuery] = useState('');
  const [selectedGroup, setSelectedGroup] = useState<string>('All');

  const groups = ['All', 'Stats', 'Change', 'Counts', 'Correlation', 'Entropy', 'Spectral'];

  const filteredFeatures = useMemo(() => {
    return FEATURES.filter((f) => {
      const matchesGroup = selectedGroup === 'All' || f.group === selectedGroup;
      const q = filterQuery.toLowerCase().trim();
      const matchesQuery =
        !q ||
        f.name.toLowerCase().includes(q) ||
        f.definition.toLowerCase().includes(q) ||
        f.notes.toLowerCase().includes(q) ||
        f.undefinedWhen.toLowerCase().includes(q);
      return matchesGroup && matchesQuery;
    });
  }, [filterQuery, selectedGroup]);

  return (
    <div className="my-8 rounded-xl border border-borderLine bg-card p-4 sm:p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-borderDim">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-ink">Interactive Feature Explorer</h2>
          <p className="text-xs text-muted mt-0.5">
            Showing {filteredFeatures.length} of {FEATURES.length} features (fixed column order 0..32)
          </p>
        </div>

        {/* Filter input */}
        <div className="relative w-full sm:w-64">
          <input
            type="text"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder="Filter features..."
            aria-label="Filter features"
            className="w-full rounded-md border border-borderLine bg-canvas px-3 py-1.5 text-xs text-ink placeholder:text-muted focus:border-ink focus:outline-none focus:ring-1 focus:ring-ink"
          />
          {filterQuery && (
            <button
              type="button"
              onClick={() => setFilterQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted hover:text-ink text-xs"
              aria-label="Clear filter"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap items-center gap-1.5 pt-3 pb-4">
        <span className="text-xs text-muted mr-1">Group:</span>
        {groups.map((group) => {
          const isActive = selectedGroup === group;
          return (
            <button
              key={group}
              type="button"
              onClick={() => setSelectedGroup(group)}
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition ${
                isActive
                  ? 'bg-ink text-white shadow-sm'
                  : 'bg-canvas text-body hover:bg-borderDim hover:text-ink'
              }`}
            >
              {group}
            </button>
          );
        })}
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-borderLine">
        <table className="w-full text-left border-collapse text-xs">
          <thead className="bg-canvas border-b border-borderLine text-ink font-semibold">
            <tr>
              <th className="px-3 py-2 text-center w-10">#</th>
              <th className="px-3 py-2">Feature</th>
              <th className="px-3 py-2">Group</th>
              <th className="px-3 py-2">Definition / Formula</th>
              <th className="px-3 py-2">Complexity</th>
              <th className="px-3 py-2">Undefined When</th>
              <th className="px-3 py-2">Implementation Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-borderDim">
            {filteredFeatures.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-muted">
                  No features match your query "{filterQuery}".
                </td>
              </tr>
            ) : (
              filteredFeatures.map((feat) => (
                <tr key={feat.name} className="hover:bg-canvas/50 transition-colors">
                  <td className="px-3 py-2.5 text-center font-mono text-muted">{feat.index}</td>
                  <td className="px-3 py-2.5 font-mono font-bold text-ink whitespace-nowrap">
                    <code>{feat.name}</code>
                  </td>
                  <td className="px-3 py-2.5">
                    <span className="inline-block rounded bg-borderDim px-1.5 py-0.5 text-[10.5px] font-semibold text-body">
                      {feat.group}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 font-mono text-[11px] text-body">{feat.definition}</td>
                  <td className="px-3 py-2.5 font-mono text-muted whitespace-nowrap">{feat.complexity}</td>
                  <td className="px-3 py-2.5 font-mono text-[11px] text-muted">{feat.undefinedWhen}</td>
                  <td className="px-3 py-2.5 text-body">{feat.notes}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
