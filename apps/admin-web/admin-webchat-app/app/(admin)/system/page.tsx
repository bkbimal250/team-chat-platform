import { Unavailable } from "@/features/admin/unavailable";
export default function Page() {
  return (
    <Unavailable
      title="System health"
      description="An authorized platform-wide infrastructure health API is not exposed. Operational checks remain local CLI tasks."
    />
  );
}
