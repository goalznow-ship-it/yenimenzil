import type { Metadata } from "next";
import { ProfilePage } from "@/features/auth/profile-page";

export const metadata: Metadata = {
  title: "Profil",
  description: "Hesab məlumatlarınızı idarə edin."
};

export default function ProfileRoute() {
  return <ProfilePage />;
}
