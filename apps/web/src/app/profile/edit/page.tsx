import type { Metadata } from "next";
import { ProfilePage } from "@/features/auth/profile-page";

export const metadata: Metadata = {
  title: "Profil məlumatları",
  description: "Hesab məlumatlarınızı yeniləyin."
};

export default function ProfileEditRoute() {
  return <ProfilePage />;
}
