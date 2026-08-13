import type { Metadata } from "next";
import { ComparePage } from "@/features/compare/compare-page";

export const metadata: Metadata = {
  title: "Müqayisə",
  description: "Seçdiyiniz elanları yan-yana müqayisə edin."
};

export default function CompareRoute() {
  return <ComparePage />;
}
