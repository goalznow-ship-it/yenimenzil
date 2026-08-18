import type { Metadata } from "next";
import { ListingEdit } from "@/features/listings/listing-edit";

export const metadata: Metadata = {
  title: "Elanı redaktə et",
  description: "Elanınızı IdealEv.az-da redaktə edin."
};

export default function EditPropertyPage() {
  return <ListingEdit />;
}
