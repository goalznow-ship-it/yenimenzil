import type { Metadata } from "next";
import { AgentProfilePage } from "@/features/agents/agent-profile-page";

export const metadata: Metadata = {
  title: "Agent profili",
  description: "Agent haqqında məlumat və onun elanları."
};

export default async function AgentProfileRoute({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <AgentProfilePage agentId={id} />;
}
