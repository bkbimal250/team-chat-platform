import type { ReactNode } from "react";
export function DataTable<T>({
  rows,
  columns,
  getRowKey,
}: {
  rows: T[];
  columns: { header: string; cell: (row: T) => ReactNode }[];
  getRowKey: (row: T) => string;
}) {
  return (
    <div tabIndex={0} role="region" aria-label="Scrollable management table" className="max-w-full overflow-x-auto rounded-lg border border-aurora-border focus-visible:outline-2 focus-visible:outline-indigo-500">
      <table className="block w-full text-sm sm:table">
        <thead className="hidden sm:table-header-group">
          <tr>
            {columns.map((c) => (
              <th scope="col" className="whitespace-nowrap bg-aurora-background px-3 py-3 text-left text-xs font-semibold text-aurora-muted" key={c.header}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="block space-y-3 sm:table-row-group sm:space-y-0">
          {rows.map((row) => (
            <tr className="block rounded-xl border border-aurora-border p-2 hover:bg-aurora-background sm:table-row sm:rounded-none sm:border-x-0 sm:border-b-0 sm:p-0" key={getRowKey(row)}>
              {columns.map((c) => (
                <td className="block max-w-full break-words px-3 py-2 align-top sm:table-cell sm:max-w-64 sm:py-3" key={c.header}>
                  <span className="mr-2 text-xs font-semibold text-aurora-muted sm:hidden">{c.header}</span>{c.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
