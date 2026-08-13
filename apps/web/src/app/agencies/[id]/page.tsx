import type { Metadata } from "next";
import { AgencyProfilePage } from "@/features/agencies/agency-profile-page";

export const metadata: Metadata = {
  title: "Agentlik profili",
  description: "Agentlik haqqında məlumat və onun elanları."
};

export default async function AgencyProfileRoute({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <AgencyProfilePage agencyId={id} />;
}
