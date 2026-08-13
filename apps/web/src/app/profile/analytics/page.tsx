import type { Metadata } from "next";
import { AnalyticsPage } from "@/features/analytics/analytics-page";

export const metadata: Metadata = {
  title: "Satış statistikası",
  description: "Elanlarınızın görünürlük və maraqlanma göstəriciləri."
};

export default function AnalyticsRoute() {
  return <AnalyticsPage />;
}
