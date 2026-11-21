import React, { useState } from "react";
import { Search, Filter } from "lucide-react";

export interface Column<T> {
  header: string;
  accessor?: keyof T;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

export interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  searchPlaceholder?: string;
  searchFilter?: (item: T, query: string) => boolean;
  categoryFilter?: {
    label: string;
    key: keyof T;
    options: { label: string; value: string }[];
  };
  actions?: React.ReactNode;
  emptyText?: string;
  keyExtractor: (item: T) => string;
}

export function DataTable<T>({
  data,
  columns,
  searchPlaceholder = "Search...",
  searchFilter,
  categoryFilter,
  actions,
  emptyText = "No items found",
  keyExtractor,
}: DataTableProps<T>) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  const filteredData = data.filter((item) => {
    if (searchQuery && searchFilter) {
      if (!searchFilter(item, searchQuery)) return false;
    }
    if (categoryFilter && selectedCategory !== "all") {
      const val = String(item[categoryFilter.key]);
      if (val !== selectedCategory) return false;
    }
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Control bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 items-center gap-3">
          {searchFilter && (
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-ink-3" />
              <input
                type="text"
                placeholder={searchPlaceholder}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-line bg-surface py-2 pl-9 pr-4 text-sm text-ink outline-none transition focus:border-brand focus:ring-1 focus:ring-brand"
              />
            </div>
          )}

          {categoryFilter && (
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-ink-3" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="rounded-lg border border-line bg-surface py-2 px-3 text-sm text-ink outline-none transition focus:border-brand"
              >
                <option value="all">All {categoryFilter.label}</option>
                {categoryFilter.options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>

      {/* Table grid */}
      <div className="overflow-hidden rounded-xl border border-line bg-paper shadow-card">
        <table className="w-full text-left text-sm text-ink">
          <thead className="border-b border-line bg-surface/60 text-xs font-semibold uppercase tracking-wider text-ink-2">
            <tr>
              {columns.map((col, idx) => (
                <th key={idx} className={`px-5 py-3.5 ${col.className || ""}`}>
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {filteredData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-5 py-8 text-center text-ink-3">
                  {emptyText}
                </td>
              </tr>
            ) : (
              filteredData.map((item) => (
                <tr key={keyExtractor(item)} className="transition hover:bg-surface/40">
                  {columns.map((col, idx) => (
                    <td key={idx} className={`px-5 py-4 ${col.className || ""}`}>
                      {col.render ? col.render(item) : col.accessor ? String(item[col.accessor] ?? "") : null}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
