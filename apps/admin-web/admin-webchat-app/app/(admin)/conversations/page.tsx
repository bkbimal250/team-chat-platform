import { Unavailable } from "@/features/admin/unavailable";
export default function Page() {
  return (
    <Unavailable
      title="Conversations"
      description="There is no organization-wide conversation administration API. User-owned conversations and private messages are not exposed in this console."
    />
  );
}
