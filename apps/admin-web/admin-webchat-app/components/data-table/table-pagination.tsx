import { Button } from "@/components/ui/button";
export function TablePagination({
  page,
  total,
  onPageChange,
}: {
  page: number;
  total: number;
  onPageChange: (n: number) => void;
}) {
  return (
    <nav aria-label="Table pages" className="mt-4 flex items-center gap-3">
      <Button
        variant="outline"
        disabled={page === 1}
        onClick={() => onPageChange(page - 1)}
      >
        Previous
      </Button>
      <span aria-current="page">Page {page}</span>
      <Button
        variant="outline"
        disabled={page >= total}
        onClick={() => onPageChange(page + 1)}
      >
        Next
      </Button>
    </nav>
  );
}
