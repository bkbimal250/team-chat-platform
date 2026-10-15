import { ChevronLeft, ChevronRight } from "lucide-react";
import { IconButton, iconSize } from "./icon-button";

export function PanelPagination({
  page,
  hasPrev,
  hasNext,
  disabled,
  onPrev,
  onNext,
}: {
  page: number;
  hasPrev: boolean;
  hasNext: boolean;
  disabled?: boolean;
  onPrev: () => void;
  onNext: () => void;
}) {
  return (
    <div className="flex items-center justify-between gap-2 border-t border-aurora-border px-3 py-2">
      <IconButton
        label="Previous page"
        disabled={!hasPrev || disabled}
        onClick={onPrev}
        className="text-aurora-muted"
      >
        <ChevronLeft className={iconSize} />
      </IconButton>
      <span className="text-xs tabular-nums text-aurora-muted">Page {page + 1}</span>
      <IconButton
        label="Next page"
        disabled={!hasNext || disabled}
        onClick={onNext}
        className="text-aurora-muted"
      >
        <ChevronRight className={iconSize} />
      </IconButton>
    </div>
  );
}
