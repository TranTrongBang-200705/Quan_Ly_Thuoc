import { Activity, Brain, Database } from "lucide-react";
import { Badge } from "../ui";

export function SystemStatusBadge({ type = "backend", status }) {
  const Icon = type === "ai" ? Brain : type === "database" ? Database : Activity;
  const isHealthy = status === "healthy" || status === "online" || status === "ready";

  const label =
    type === "ai"
      ? isHealthy
        ? "AI Ready"
        : "AI Fallback"
      : type === "database"
        ? isHealthy
          ? "Database Connected"
          : "Database Check"
        : isHealthy
          ? "Backend Online"
          : "Backend Offline";

  const tone =
    type === "ai"
      ? isHealthy ? "teal" : "amber"
      : type === "database"
        ? isHealthy ? "cyan" : "amber"
        : isHealthy ? "emerald" : "red";

  return (
    <Badge tone={tone} dot={isHealthy}>
      <Icon size={13} />
      {label}
    </Badge>
  );
}
