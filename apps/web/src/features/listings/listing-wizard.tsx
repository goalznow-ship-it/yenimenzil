"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Button, Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@yenimenzil/ui";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Check,
  CircleCheck,
  Clock3,
  Home,
  ImageIcon,
  Info,
  MapPin,
  Send,
  Tag,
  Trash2,
  Upload
} from "lucide-react";
import { RequireAuth } from "@/components/auth/auth-provider";
import { CITIES, DISTRICTS, METRO_STATIONS } from "@/data/locations";
import { listingWriteApi, type ListingInput, type ListingDetail } from "@/services/listing-write-api";
import { MapView } from "@/features/map/map-view";
import { useAuth } from "@/store/auth";

const PROPERTY_TYPES = [
  { value: "apartment", label: "Mənzil" },
  { value: "new_building", label: "Yeni tikili" },
  { value: "old_building", label: "Köhnə tikili" },
  { value: "house", label: "Həyət evi" },
  { value: "villa", label: "Villa" },
  { value: "land", label: "Torpaq" },
  { value: "office", label: "Ofis" },
  { value: "commercial", label: "Obyekt" },
  { value: "garage", label: "Qaraj" }
] as const;

const DEAL_TYPES = [
  { value: "sale", label: "Satıram", hint: "Əmlakı satmaq istəyirəm" },
  { value: "rent", label: "Kirayə verirəm", hint: "Uzunmüddətli kirayə" },
  { value: "daily", label: "Günlük verirəm", hint: "Günlük kirayə" }
] as const;

const REPAIR_STATUSES = [
  { value: "renovated", label: "Yenilənmiş" },
  { value: "cosmetic", label: "Kosmetik təmir" },
  { value: "needs_repair", label: "Təmirə ehtiyacı var" },
  { value: "none", label: "Təmir yoxdur" }
] as const;

const DOCUMENT_TYPES = [
  { value: "citizenship", label: "Vətəndaşlıq" },
  { value: "extract", label: "Çıxarış" },
  { value: "certificate", label: "Şəhadətnamə" }
] as const;

const FEATURE_OPTIONS = [
  { value: "elevator", label: "Lift" },
  { value: "parking", label: "Dayanacaq" },
  { value: "furnished", label: "Mebelli" },
  { value: "balcony", label: "Balkon" },
  { value: "renovation", label: "Təmir" },
  { value: "pool", label: "Hovuz" },
  { value: "garden", label: "Həyət" },
  { value: "security", label: "Mühafizə" },
  { value: "internet", label: "İnternet" },
  { value: "mortgage", label: "İpoteka" },
  { value: "exchange", label: "Mübadilə" }
] as const;

const STEPS = ["Əmlak", "Yerləşmə", "Qiymət", "Detallar", "Fotoşəkillər", "Mətn", "Baxış"];

const FIELD_CLS =
  "w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm outline-none transition-colors placeholder:text-foreground/35 focus:border-brand/60 focus:ring-2 focus:ring-brand/15";
const LABEL_CLS = "mb-1.5 block text-[13px] font-medium text-foreground/75";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className={LABEL_CLS}>{label}</label>
      {children}
    </div>
  );
}

function StepButton({
  active,
  done,
  index,
  label
}: {
  active: boolean;
  done: boolean;
  index: number;
  label: string;
}) {
  return (
    <div className="flex flex-1 flex-col items-center gap-1.5">
      <span
        className={
          "flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold " +
          (active
            ? "bg-brand text-white"
            : done
              ? "bg-brand-soft text-brand"
              : "bg-foreground/[0.06] text-foreground/40")
        }
      >
        {done ? <Check className="h-3.5 w-3.5" /> : index + 1}
      </span>
      <span
        className={
          "hidden text-[11px] font-medium md:block " +
          (active ? "text-brand" : "text-foreground/45")
        }
      >
        {label}
      </span>
    </div>
  );
}

interface WizardState {
  deal_type: "sale" | "rent" | "daily";
  property_type: string;
  seller_kind: "owner" | "agent";
  city: string;
  district: string;
  metro: string;
  address_text: string;
  latitude: number;
  longitude: number;
  price: string;
  currency: "AZN" | "USD" | "EUR";
  rooms: string;
  bedrooms: string;
  bathrooms: string;
  area_total: string;
  floor: string;
  total_floors: string;
  building_type: "new" | "old" | "";
  repair_status: string;
  document_type: string;
  mortgage_available: boolean;
  features: string[];
  mediaUrls: string[];
  title: string;
  description: string;
}

const INITIAL: WizardState = {
  deal_type: "sale",
  property_type: "apartment",
  seller_kind: "owner",
  city: "Bakı",
  district: "",
  metro: "",
  address_text: "",
  latitude: 40.4093,
  longitude: 49.8671,
  price: "",
  currency: "AZN",
  rooms: "",
  bedrooms: "",
  bathrooms: "",
  area_total: "",
  floor: "",
  total_floors: "",
  building_type: "new",
  repair_status: "",
  document_type: "",
  mortgage_available: false,
  features: [],
  mediaUrls: [],
  title: "",
  description: ""
};

function hasDraftContent(state: Partial<WizardState>, step = 0) {
  return Boolean(
    step > 0 ||
      state.address_text ||
      state.price ||
      state.rooms ||
      state.area_total ||
      state.title ||
      state.description ||
      state.mediaUrls?.length
  );
}

function fromDetail(d: ListingDetail): WizardState {
  return {
    deal_type: d.deal_type,
    property_type: d.property_type,
    seller_kind: "owner",
    city: d.location?.city ?? "Bakı",
    district: d.location?.district ?? "",
    metro: d.location?.metro ?? "",
    address_text: d.location?.address_text ?? "",
    latitude: d.location?.latitude ?? 40.4093,
    longitude: d.location?.longitude ?? 49.8671,
    price: d.price != null ? String(d.price) : "",
    currency: d.currency,
    rooms: d.rooms != null ? String(d.rooms) : "",
    bedrooms: d.bedrooms != null ? String(d.bedrooms) : "",
    bathrooms: d.bathrooms != null ? String(d.bathrooms) : "",
    area_total: d.area_total != null ? String(d.area_total) : "",
    floor: d.floor != null ? String(d.floor) : "",
    total_floors: d.total_floors != null ? String(d.total_floors) : "",
    building_type: d.building_type ?? "new",
    repair_status: d.repair_status ?? "",
    document_type: d.document_type ?? "",
    mortgage_available: d.mortgage_available,
    features: d.features ?? [],
    mediaUrls: (d.media ?? []).map((m) => m.url),
    title: d.title,
    description: d.description ?? ""
  };
}

export function ListingWizard({
  listingId,
  initialListing
}: {
  listingId?: string;
  initialListing?: ListingDetail;
}) {
  const [step, setStep] = React.useState(0);
  const [state, setState] = React.useState<WizardState>(() =>
    initialListing ? fromDetail(initialListing) : INITIAL
  );
  const [error, setError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);
  const [uploading, setUploading] = React.useState(false);
  const [draftReady, setDraftReady] = React.useState(Boolean(listingId));
  const [draftRestored, setDraftRestored] = React.useState(false);
  const [done, setDone] = React.useState(false);
  const router = useRouter();
  const user = useAuth((auth) => auth.user);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (listingId || initialListing) return;
    try {
      const raw = window.localStorage.getItem("yenimenzil-listing-draft-v1");
      if (raw) {
        const draft = JSON.parse(raw) as { state?: Partial<WizardState>; step?: number };
        if (draft.state && hasDraftContent(draft.state, draft.step)) {
          setState({ ...INITIAL, ...draft.state });
          setStep(Math.min(Math.max(draft.step ?? 0, 0), STEPS.length - 1));
          setDraftRestored(true);
        }
      }
    } catch {
      window.localStorage.removeItem("yenimenzil-listing-draft-v1");
    } finally {
      setDraftReady(true);
    }
  }, [initialListing, listingId]);

  React.useEffect(() => {
    if (!draftReady || listingId || done) return;
    if (!hasDraftContent(state, step)) {
      window.localStorage.removeItem("yenimenzil-listing-draft-v1");
      return;
    }
    window.localStorage.setItem(
      "yenimenzil-listing-draft-v1",
      JSON.stringify({ state, step, savedAt: Date.now() })
    );
  }, [draftReady, done, listingId, state, step]);

  const set = <K extends keyof WizardState>(key: K, value: WizardState[K]) =>
    setState((s) => ({ ...s, [key]: value }));

  const toggleFeature = (code: string) =>
    setState((s) => ({
      ...s,
      features: s.features.includes(code)
        ? s.features.filter((f) => f !== code)
        : [...s.features, code]
    }));

  const uploadMedia = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (!selected.length) return;
    if (selected.length > 10) {
      setError("Bir dəfəyə maksimum 10 şəkil seçin");
      return;
    }
    if (state.mediaUrls.length + selected.length > 30) {
      setError("Elana maksimum 30 şəkil əlavə etmək olar");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const uploaded = await listingWriteApi.uploadTemp(selected);
      setState((current) => ({
        ...current,
        mediaUrls: [...current.mediaUrls, ...uploaded.map((item) => item.url)]
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Şəkillər yüklənə bilmədi");
    } finally {
      setUploading(false);
    }
  };

  const stepValid = (): string | null => {
    switch (step) {
      case 0:
        return state.property_type ? null : "Əmlak növü seçin";
      case 1:
        return state.address_text.trim()
          ? null
          : "Ünvan məlumatını daxil edin";
      case 2:
        return state.price && Number(state.price) > 0
          ? null
          : "Düzgün qiymət daxil edin";
      case 3:
        return state.area_total &&
          Number(state.area_total) > 0 &&
          (state.property_type === "land" || (state.rooms && Number(state.rooms) > 0))
          ? null
          : state.property_type === "land"
            ? "Torpaq sahəsini daxil edin"
            : "Otaq sayı və sahəni daxil edin";
      case 4:
        return state.mediaUrls.length >= 4
          ? null
          : "Elana ən azı 4 fotoşəkil əlavə edin";
      case 5:
        return state.title.trim().length >= 3
          ? null
          : "Başlıq ən azı 3 simvol olmalıdır";
      default:
        return null;
    }
  };

  const next = () => {
    const problem = stepValid();
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };

  const submit = async () => {
    if (!user?.profile?.phone_verified) {
      setError("Elan yerləşdirmək üçün profilinizdə telefon nömrəsini təsdiqləyin");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const input: ListingInput = {
        title: state.title,
        description: state.description,
        deal_type: state.deal_type,
        property_type: state.property_type,
        price: Number(state.price),
        currency: state.currency,
        seller_kind: state.seller_kind,
        rooms: Number(state.rooms) || 0,
        bedrooms: state.bedrooms ? Number(state.bedrooms) : undefined,
        bathrooms: state.bathrooms ? Number(state.bathrooms) : undefined,
        area_total: Number(state.area_total),
        floor: state.floor ? Number(state.floor) : undefined,
        total_floors: state.total_floors ? Number(state.total_floors) : undefined,
        building_type: state.building_type || undefined,
        repair_status: state.repair_status || undefined,
        document_type: state.document_type || undefined,
        mortgage_available: state.mortgage_available,
        features: state.features,
        location: {
          latitude: state.latitude,
          longitude: state.longitude,
          address_text: state.address_text,
          city: state.city,
          district: state.district || undefined,
          metro: state.metro || undefined
        },
        media: state.mediaUrls
          .filter((u) => u.trim())
          .map((url, i) => ({ url: url.trim(), is_cover: i === 0 }))
      };
      if (listingId) {
        await listingWriteApi.update(listingId, input);
      } else {
        const created = await listingWriteApi.create(input);
        await listingWriteApi.submit(created.id);
      }
      window.localStorage.removeItem("yenimenzil-listing-draft-v1");
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Elan yaradıla bilmədi");
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <div className="mx-auto flex w-full max-w-xl flex-col items-center px-4 py-20 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-soft">
          <Check className="h-7 w-7 text-brand" />
        </div>
        <h1 className="mt-5 text-2xl font-semibold">
          {listingId ? "Elan yeniləndi" : "Elan göndərildi"}
        </h1>
        <p className="mt-2 max-w-md text-sm text-muted-foreground">
          {listingId
            ? "Dəyişikliklər yadda saxlanıldı. Elanınızın vəziyyəti qorunub saxlanıldı."
            : "Elanınız baxış üçün moderatora göndərildi. Təsdiqləndikdən sonra dərc olunacaq və sizə bildiriş göndəriləcək."}
        </p>
        <div className="mt-6 flex gap-3">
          <Button variant="outline" onClick={() => router.push("/profile")}>
            İdarə panelim
          </Button>
          <Button onClick={() => router.push("/")}>Ana səhifə</Button>
        </div>
      </div>
    );
  }

  return (
    <RequireAuth>
      <div className="mx-auto w-full max-w-6xl px-4 py-8 lg:px-6">
        <div className="mb-7 border-b border-border pb-5">
        <h1 className="text-3xl font-semibold tracking-tight">Yeni elan</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Məlumatları düzgün daxil edin — elanınız daha tez təsdiqlənəcək.
        </p>
        </div>
        {draftRestored ? (
          <div className="mt-4 rounded-xl bg-brand-soft px-4 py-3 text-sm text-brand">
            Yarımçıq qalan elan qaralamanız bərpa edildi.
          </div>
        ) : null}

        <div className="mb-7 flex items-start gap-1 rounded-2xl border border-border bg-surface px-4 py-4 shadow-sm">
          {STEPS.map((label, i) => (
            <StepButton
              key={label}
              index={i}
              label={label}
              active={step === i}
              done={step > i}
            />
          ))}
        </div>

        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="rounded-2xl bg-surface p-6 shadow-sm ring-1 ring-border/70 md:p-8">
          {step === 0 ? (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold">Elanınız haqqında</h2>
                <p className="mb-4 mt-1 text-sm text-muted-foreground">Əvvəlcə əməliyyat və əmlak növünü seçin.</p>
                <span className={LABEL_CLS}>Nə etmək istəyirsiniz?</span>
                <div className="grid gap-3 sm:grid-cols-3">
                  {DEAL_TYPES.map((deal) => (
                    <button
                      key={deal.value}
                      type="button"
                      onClick={() => set("deal_type", deal.value)}
                      className={
                        "rounded-xl border px-3 py-2.5 text-sm font-medium transition-colors " +
                        (state.deal_type === deal.value
                          ? "border-brand/40 bg-brand-soft text-brand"
                          : "border-border text-foreground/65 hover:border-foreground/20")
                      }
                    >
                      <span className="block text-sm font-semibold">{deal.label}</span>
                      <span className="mt-1 block text-xs font-normal opacity-65">{deal.hint}</span>
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <span className={LABEL_CLS}>Əmlak növü</span>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                  {PROPERTY_TYPES.map((type) => (
                    <button
                      key={type.value}
                      type="button"
                      onClick={() => set("property_type", type.value)}
                      className={
                        "flex min-h-20 flex-col items-center justify-center gap-2 rounded-xl border px-3 py-3 text-sm font-medium transition-all " +
                        (state.property_type === type.value
                          ? "border-brand/40 bg-brand-soft text-brand"
                          : "border-border text-foreground/65 hover:border-foreground/20")
                      }
                    >
                      {type.value === "house" || type.value === "villa" ? <Home className="h-5 w-5" /> : <Building2 className="h-5 w-5" />}
                      {type.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <span className={LABEL_CLS}>Elanı kim yerləşdirir?</span>
                <div className="grid grid-cols-2 gap-2">
                  {([
                    ["owner", "Elanın sahibiyəm"],
                    ["agent", "Mən vasitəçiyəm"]
                  ] as const).map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => set("seller_kind", value)}
                      className={
                        "rounded-xl border p-4 text-left transition-all " +
                        (state.seller_kind === value
                          ? "border-brand/40 bg-brand-soft text-brand"
                          : "border-border text-foreground/65 hover:border-foreground/20")
                      }
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : null}

          {step === 1 ? (
            <div className="space-y-4">
              <Field label="Şəhər">
                <Select value={state.city} onValueChange={(v) => set("city", v)}>
                  <SelectTrigger className={FIELD_CLS}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CITIES.map((city) => (
                      <SelectItem key={city.name} value={city.name}>
                        {city.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Rayon">
                <Select
                  value={state.district}
                  onValueChange={(v) => set("district", v)}
                >
                  <SelectTrigger className={FIELD_CLS}>
                    <SelectValue placeholder="Seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {Array.from(
                      new Set(
                        DISTRICTS.filter((d) => d.city === state.city).map(
                          (d) => d.district
                        )
                      )
                    ).map((district) => (
                      <SelectItem key={district} value={district}>
                        {district}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Metro (könüllü)">
                <Select value={state.metro} onValueChange={(v) => set("metro", v)}>
                  <SelectTrigger className={FIELD_CLS}>
                    <SelectValue placeholder="Seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {METRO_STATIONS.map((metro) => (
                      <SelectItem key={metro} value={metro}>
                        {metro}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Ünvan">
                <div className="relative">
                  <MapPin className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/35" />
                  <Input
                    className="pl-9"
                    placeholder="Küçə, ev nömrəsi"
                    value={state.address_text}
                    onChange={(e) => set("address_text", e.target.value)}
                  />
                </div>
              </Field>
              <div>
                <span className={LABEL_CLS}>Xəritədə dəqiq yeri göstərin</span>
                <p className="mb-2 text-xs text-muted-foreground">Elanın yerini dəyişmək üçün xəritənin üzərinə klikləyin.</p>
                <MapView
                  className="h-72 overflow-hidden rounded-xl border border-border"
                  center={{ lat: state.latitude, lng: state.longitude }}
                  zoom={14}
                  markers={[{ id: "selected-location", point: { lat: state.latitude, lng: state.longitude }, price: 0, formattedPrice: "Seçilmiş yer" }]}
                  onMapClick={(point) => setState((current) => ({ ...current, latitude: point.lat, longitude: point.lng }))}
                />
                <p className="mt-2 text-xs text-foreground/50">{state.latitude.toFixed(5)}, {state.longitude.toFixed(5)}</p>
              </div>
            </div>
          ) : null}

          {step === 2 ? (
            <div className="space-y-4">
              <div className="grid grid-cols-[1fr_110px] gap-3">
                <Field label="Qiymət">
                  <div className="relative">
                    <Tag className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/35" />
                    <Input
                      className="pl-9"
                      type="number"
                      min={1}
                      inputMode="numeric"
                      placeholder="150000"
                      value={state.price}
                      onChange={(e) => set("price", e.target.value)}
                    />
                  </div>
                </Field>
                <Field label="Valyuta">
                  <Select
                    value={state.currency}
                    onValueChange={(v) =>
                      set("currency", v as WizardState["currency"])
                    }
                  >
                    <SelectTrigger className={FIELD_CLS}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="AZN">AZN</SelectItem>
                      <SelectItem value="USD">USD</SelectItem>
                      <SelectItem value="EUR">EUR</SelectItem>
                    </SelectContent>
                  </Select>
                </Field>
              </div>
              <label className="flex items-center gap-2.5 text-sm text-foreground/75">
                <input
                  type="checkbox"
                  className="h-4 w-4 accent-brand"
                  checked={state.mortgage_available}
                  onChange={(e) => set("mortgage_available", e.target.checked)}
                />
                İpoteka mümkündür
              </label>
            </div>
          ) : null}

          {step === 3 ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              {state.property_type !== "land" ? <Field label="Otaq sayı">
                <Input
                  type="number"
                  min={0}
                  value={state.rooms}
                  onChange={(e) => set("rooms", e.target.value)}
                />
              </Field> : null}
              {state.property_type !== "land" ? <Field label="Yataq otağı">
                <Input
                  type="number"
                  min={0}
                  value={state.bedrooms}
                  onChange={(e) => set("bedrooms", e.target.value)}
                />
              </Field> : null}
              {state.property_type !== "land" ? <Field label="Hamam">
                <Input
                  type="number"
                  min={0}
                  value={state.bathrooms}
                  onChange={(e) => set("bathrooms", e.target.value)}
                />
              </Field> : null}
              <Field label={state.property_type === "land" ? "Torpaq sahəsi (sot)" : "Sahə (m²)"}>
                <Input
                  type="number"
                  min={1}
                  value={state.area_total}
                  onChange={(e) => set("area_total", e.target.value)}
                />
              </Field>
              {!["land", "house", "villa", "garage"].includes(state.property_type) ? <Field label="Mərtəbə">
                <Input
                  type="number"
                  min={0}
                  value={state.floor}
                  onChange={(e) => set("floor", e.target.value)}
                />
              </Field> : null}
              {!["land", "house", "villa", "garage"].includes(state.property_type) ? <Field label="Mərtəbə sayı">
                <Input
                  type="number"
                  min={0}
                  value={state.total_floors}
                  onChange={(e) => set("total_floors", e.target.value)}
                />
              </Field> : null}
              {!["land", "house", "villa", "garage"].includes(state.property_type) ? <Field label="Bina">
                <Select
                  value={state.building_type}
                  onValueChange={(v) => set("building_type", v as "new" | "old")}
                >
                  <SelectTrigger className={FIELD_CLS}>
                    <SelectValue placeholder="Seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="new">Yeni</SelectItem>
                    <SelectItem value="old">Köhnə</SelectItem>
                  </SelectContent>
                </Select>
              </Field> : null}
              <Field label="Təmir">
                <Select
                  value={state.repair_status}
                  onValueChange={(v) => set("repair_status", v)}
                >
                  <SelectTrigger className={FIELD_CLS}>
                    <SelectValue placeholder="Seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {REPAIR_STATUSES.map((r) => (
                      <SelectItem key={r.value} value={r.value}>
                        {r.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Sənəd">
                <Select
                  value={state.document_type}
                  onValueChange={(v) => set("document_type", v)}
                >
                  <SelectTrigger className={FIELD_CLS}>
                    <SelectValue placeholder="Seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {DOCUMENT_TYPES.map((d) => (
                      <SelectItem key={d.value} value={d.value}>
                        {d.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
            </div>
          ) : null}

          {step === 4 ? (
            <div className="space-y-4">
              <p className="flex items-center gap-2 text-sm text-muted-foreground">
                <Info className="h-4 w-4" />
                Minimum 4, maksimum 30 real fotoşəkil. Loqo, mətn, çərçivə və
                ekran görüntüsü olan şəkillər qəbul edilmir.
              </p>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={uploadMedia}
              />
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {state.mediaUrls.map((url, i) => (
                  <div key={url} className="group relative aspect-[4/3] overflow-hidden rounded-xl bg-foreground/[0.04] ring-1 ring-border">
                    {/* Remote storage URLs are user uploads, so native img is intentional. */}
                    <img src={url} alt={`Elan şəkli ${i + 1}`} className="h-full w-full object-cover" />
                    {i === 0 ? <span className="absolute left-2 top-2 rounded-md bg-brand px-2 py-1 text-[10px] font-semibold text-white">Əsas şəkil</span> : null}
                    <button
                      type="button"
                      onClick={() =>
                        set(
                          "mediaUrls",
                          state.mediaUrls.filter((_, j) => j !== i)
                        )
                      }
                      aria-label="Şəkli sil"
                      className="absolute right-2 top-2 rounded-lg bg-black/65 p-2 text-white hover:bg-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading || state.mediaUrls.length >= 30}
                className="gap-2"
              >
                {uploading ? <ImageIcon className="h-4 w-4 animate-pulse" /> : <Upload className="h-4 w-4" />}
                {uploading ? "Yüklənir…" : "Şəkilləri seç"} ({state.mediaUrls.length}/30)
              </Button>
            </div>
          ) : null}

          {step === 5 ? (
            <div className="space-y-4">
              <Field label="Başlıq">
                <Input
                  placeholder="Məs: Nərimanovda 3 otaqlı mənzil"
                  value={state.title}
                  onChange={(e) => set("title", e.target.value)}
                />
              </Field>
              <Field label="Təsvir">
                <textarea
                  rows={6}
                  className={FIELD_CLS}
                  placeholder="Elan haqqında ətraflı məlumat…"
                  value={state.description}
                  onChange={(e) => set("description", e.target.value)}
                />
              </Field>
              <div>
                <span className={LABEL_CLS}>Əlavə xüsusiyyətlər</span>
                <div className="flex flex-wrap gap-2">
                  {FEATURE_OPTIONS.map((feature) => {
                    const active = state.features.includes(feature.value);
                    return (
                      <button
                        key={feature.value}
                        type="button"
                        onClick={() => toggleFeature(feature.value)}
                        className={
                          "rounded-full border px-3.5 py-1.5 text-[13px] font-medium transition-colors " +
                          (active
                            ? "border-brand/40 bg-brand-soft text-brand"
                            : "border-border text-foreground/65 hover:border-foreground/20")
                        }
                      >
                        {feature.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : null}

          {step === 6 ? (
            <div className="space-y-4">
              <div className="flex items-start gap-3 rounded-xl bg-foreground/[0.03] p-4 text-sm">
                <Building2 className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
                <div>
                  <p className="font-semibold text-foreground">{state.title}</p>
                  <p className="mt-0.5 text-muted-foreground">
                    {state.deal_type === "sale"
                      ? "Satış"
                      : state.deal_type === "rent"
                        ? "Kirayə"
                        : "Günlük"}{" "}
                    · {PROPERTY_TYPES.find((t) => t.value === state.property_type)?.label} ·{" "}
                    {state.rooms} otaq · {state.area_total} m²
                  </p>
                  <p className="mt-0.5 font-semibold text-brand">
                    {Number(state.price).toLocaleString("az-AZ")} {state.currency}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {state.address_text}
                    {state.metro ? ` · ${state.metro}` : ""}
                  </p>
                </div>
              </div>
              {state.features.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {state.features.map((f) => (
                    <span
                      key={f}
                      className="rounded-full bg-brand-soft px-2.5 py-1 text-xs font-medium text-brand"
                    >
                      {FEATURE_OPTIONS.find((o) => o.value === f)?.label ?? f}
                    </span>
                  ))}
                </div>
              ) : null}
              <p className="text-[13px] leading-relaxed text-foreground/60">
                Elan təsdiqə göndərildikdən sonra moderator tərəfindən yoxlanılır.
                Təsdiqlənmiş elan dərhal axtarışda görünür.
              </p>
            </div>
          ) : null}

          {error ? (
            <div className="mt-5 flex items-center gap-2 rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">
              <Info className="h-4 w-4 shrink-0" />
              {error}
            </div>
          ) : null}

          <div className="mt-7 flex items-center justify-between border-t border-border/70 pt-5">
            <Button
              type="button"
              variant="outline"
              onClick={() => setStep((s) => Math.max(0, s - 1))}
              disabled={step === 0}
              className="gap-1.5"
            >
              <ArrowLeft className="h-4 w-4" />
              Geri
            </Button>
            {step < STEPS.length - 1 ? (
              <Button type="button" onClick={next} className="gap-1.5">
                Növbəti
                <ArrowRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button
                type="button"
                onClick={submit}
                disabled={submitting}
                className="gap-1.5"
              >
                <Send className="h-4 w-4" />
                {submitting ? "Göndərilir…" : "Təsdiqə göndər"}
              </Button>
            )}
          </div>
        </div>
        <aside className="space-y-4 lg:sticky lg:top-24">
          <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
            <h3 className="font-semibold">Elan yerləşdirmə qaydaları</h3>
            <div className="mt-4 space-y-4 text-sm text-foreground/70">
              <p className="flex gap-3"><CircleCheck className="mt-0.5 h-4 w-4 shrink-0 text-brand" /> Düzgün ünvan və real qiymət göstərin.</p>
              <p className="flex gap-3"><ImageIcon className="mt-0.5 h-4 w-4 shrink-0 text-brand" /> Ən azı 4 keyfiyyətli foto əlavə edin.</p>
              <p className="flex gap-3"><Clock3 className="mt-0.5 h-4 w-4 shrink-0 text-brand" /> Elan yoxlamadan sonra dərc olunur.</p>
            </div>
          </div>
          <div className="rounded-2xl bg-brand-soft p-5 text-sm text-brand">
            <p className="font-semibold">Qaralamanız qorunur</p>
            <p className="mt-1 opacity-80">Səhifədən çıxsanız belə məlumatlar avtomatik saxlanılır.</p>
          </div>
        </aside>
        </div>
      </div>
    </RequireAuth>
  );
}
