"use client";

import { ResourceScreen, type ResourceRemoteAction } from "@/workspace/features/admin/resource-screen";
import { WorkspaceDetailPane } from "./workspace-detail-pane";
import type { WorkspaceRow } from "./workspace-list-panel";

export function WorkspaceResourceMain({
  resource,
  selected,
  action,
  onAction,
  onModalClose,
}: {
  resource: string;
  selected: WorkspaceRow | null;
  action: ResourceRemoteAction | null;
  onAction: (next: ResourceRemoteAction) => void;
  onModalClose: () => void;
}) {
  return (
    <>
      <WorkspaceDetailPane resource={resource} selected={selected} onAction={onAction} />
      <ResourceScreen
        resource={resource}
        hideTable
        remoteAction={action}
        onModalClose={onModalClose}
      />
    </>
  );
}
