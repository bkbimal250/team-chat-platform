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
    <div tabIndex={0} role="region" aria-label="Scrollable management table" className="max-w-full overflow-x-auto rounded-lg border border-slate-200 focus-visible:outline-2 focus-visible:outline-indigo-500">
      <table className="w-full text-sm">
        <thead>
          <tr>
            {columns.map((c) => (
              <th scope="col" className="whitespace-nowrap bg-slate-50 px-3 py-3 text-left text-xs font-semibold text-slate-600" key={c.header}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr className="border-t border-slate-100 hover:bg-slate-50" key={getRowKey(row)}>
              {columns.map((c) => (
                <td className="max-w-64 break-words px-3 py-3 align-top" key={c.header}>
                  {c.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
