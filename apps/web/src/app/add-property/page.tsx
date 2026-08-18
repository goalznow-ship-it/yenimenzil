import type { Metadata } from "next";
import { ListingWizard } from "@/features/listings/listing-wizard";

export const metadata: Metadata = {
  title: "Elan yerləşdir",
  description: "Daşınmaz əmlak elanınızı IdealEv.az-da yerləşdirin."
};

export default function AddPropertyPage() {
  return <ListingWizard />;
}
