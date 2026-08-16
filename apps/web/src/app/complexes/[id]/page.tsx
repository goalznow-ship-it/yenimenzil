import { notFound } from "next/navigation";
import {
  Building2,
  CalendarClock,
  MapPin,
  ShieldCheck,
  Users
} from "lucide-react";
import {
  COMPLEX_STATUS_LABELS
} from "@yenimenzil/types";
import type { ComplexDetail } from "@yenimenzil/types";
import { fetchComplexById } from "@/services/complex-api";
import { PropertyCard } from "@/features/properties/property-card";

async function loadComplex(id: string): Promise<ComplexDetail | undefined> {
  return fetchComplexById(id);
}

export async function generateMetadata({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const complex = await loadComplex(id);
  if (!complex) return {};
  return {
    title: `${complex.name} — YeniMenzil`,
    description:
      complex.description ??
      `${complex.name} rezidans kompleksi: ${complex.propertiesCount} elan, ${complex.unitsAvailable} mənzil.`
  };
}

export default async function ComplexPage({
  params
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const complex = await loadComplex(id);
  if (!complex) return notFound();

  const statusLabel = COMPLEX_STATUS_LABELS[complex.status];
  const statusColor =
    complex.status === "ready"
      ? "bg-green-100 text-green-700"
      : complex.status === "under_construction"
        ? "bg-amber-100 text-amber-700"
        : "bg-blue-100 text-blue-700";

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="h-56 w-full overflow-hidden bg-gray-200 md:h-72">
        {complex.coverImage ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={complex.coverImage}
            alt={complex.name}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-indigo-600 to-purple-700">
            <Building2 className="h-16 w-16 text-white/80" />
          </div>
        )}
      </div>

      <div className="mx-auto max-w-6xl px-4 pb-16">
        <div className="-mt-10 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900">
                  {complex.name}
                </h1>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${statusColor}`}
                >
                  {statusLabel}
                </span>
                {complex.isVerified && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                    <ShieldCheck className="h-3.5 w-3.5" />
                    Təsdiqlənmiş
                  </span>
                )}
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-gray-500">
                {complex.developerName && (
                  <span className="inline-flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    {complex.developerName}
                  </span>
                )}
                {(complex.city || complex.district) && (
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="h-4 w-4" />
                    {[complex.city, complex.district].filter(Boolean).join(", ")}
                  </span>
                )}
                {complex.completionYear && (
                  <span className="inline-flex items-center gap-1">
                    <CalendarClock className="h-4 w-4" />
                    {complex.status === "ready"
                      ? "Tamamlanıb"
                      : "Bitmə ili"}: {complex.completionYear}
                  </span>
                )}
              </div>
            </div>
            <div className="flex gap-8 rounded-xl bg-gray-50 px-6 py-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {complex.totalUnits ?? "—"}
                </div>
                <div className="text-xs text-gray-500">Ümumi mənzil</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-indigo-600">
                  {complex.unitsAvailable}
                </div>
                <div className="text-xs text-gray-500">Satışda</div>
              </div>
            </div>
          </div>

          {complex.description && (
            <p className="mt-4 text-sm leading-relaxed text-gray-600">
              {complex.description}
            </p>
          )}

          {complex.amenities.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {complex.amenities.map((amenity) => (
                <span
                  key={amenity}
                  className="rounded-full border border-gray-200 px-3 py-1 text-xs text-gray-600"
                >
                  {amenity}
                </span>
              ))}
            </div>
          )}
        </div>

        <h2 className="mt-10 mb-4 text-lg font-semibold text-gray-900">
          Kompleksdə elanlar ({complex.properties.length})
        </h2>
        {complex.properties.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-10 text-center text-sm text-gray-500">
            Bu kompleksdə hazırda aktiv elan yoxdur.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {complex.properties.map((property) => (
              <PropertyCard key={property.id} property={property} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}