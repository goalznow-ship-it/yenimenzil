import type { Metadata } from "next";
import { Suspense } from "react";
import { DashboardPage } from "@/features/dashboard/dashboard-page";

export const metadata: Metadata = {
  title: "İdarə paneli",
  description: "Elanlarınızı, axtarışlarınızı və hesabınızı idarə edin."
};

export default function ProfileRoute() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <DashboardPage />
    </Suspense>
  );
}
