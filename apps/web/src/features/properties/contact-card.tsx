"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import type { Property } from "@yenimenzil/types";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
  Badge,
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle
} from "@yenimenzil/ui";
import {
  BadgeCheck,
  CalendarClock,
  Check,
  MessageCircle,
  Phone,
  ShieldCheck,
  Store,
  UserRound
} from "lucide-react";
import { formatPhoneDisplay } from "@/lib/format";
import { track } from "@/services/analytics";
import { cn } from "@yenimenzil/ui";

const SELLER_PHONES: Record<string, string> = {
  "usr-101": "+994512456789",
  "usr-102": "+994553456780",
  "usr-103": "+994502334455",
  "usr-104": "+994702341516",
  "usr-105": "+994552787899",
  "usr-106": "+994552117766"
};

function sellerPhone(property: Property): string {
  return (
    SELLER_PHONES[property.seller.id] ??
    "+994500000000"
  );
}

function initials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("");
}

export function ContactCard({ property }: { property: Property }) {
  const router = useRouter();
  const [revealed, setRevealed] = React.useState(false);
  const [viewingOpen, setViewingOpen] = React.useState(false);
  const [viewingSent, setViewingSent] = React.useState(false);
  const seller = property.seller;
  const phone = sellerPhone(property);

  const revealPhone = () => {
    if (!revealed) {
      setRevealed(true);
      track("PHONE_REVEAL", { propertyId: property.id, sellerId: seller.id });
    }
  };

  const whatsappHref = `https://wa.me/${phone.replace(/\D/g, "")}?text=${encodeURIComponent(
    `Salam, "${property.title}" elanı ilə bağlı maraqlanıram (IdealEv.az).`
  )}`;

  return (
    <div className="rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70">
      <div className="flex items-center gap-3.5">
        <Avatar className="h-12 w-12">
          <AvatarImage src={seller.avatarUrl} alt={seller.name} />
          <AvatarFallback>{initials(seller.name)}</AvatarFallback>
        </Avatar>
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 truncate text-[15px] font-semibold text-foreground">
            {seller.name}
            {seller.verifiedIdentity ? (
              <BadgeCheck className="h-4 w-4 shrink-0 text-brand" />
            ) : null}
          </p>
          <p className="flex items-center gap-1.5 truncate text-[13px] text-muted-foreground">
            {seller.kind === "owner" ? (
              "Mülkiyyətçi"
            ) : (
              <>
                <Store className="h-3.5 w-3.5" />
                {seller.agencyName}
              </>
            )}
          </p>
        </div>
      </div>

      <div className="mt-2 flex flex-wrap gap-2">
        {seller.kind !== "owner" && seller.id ? (
          <Link
            href={`/agencies/${seller.id}`}
            className="inline-flex items-center gap-1 text-[12.5px] font-medium text-brand transition-colors hover:text-brand-hover"
          >
            Agentliyin profili
          </Link>
        ) : null}
        {seller.kind === "agent" && seller.id ? (
          <Link
            href={`/agents/${seller.id}`}
            className="inline-flex items-center gap-1 text-[12.5px] font-medium text-brand transition-colors hover:text-brand-hover"
          >
            Agentin profili
          </Link>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {seller.verifiedPhone ? (
          <Badge variant="green" className="gap-1">
            <Phone className="h-3 w-3" />
            Telefon təsdiqlənib
          </Badge>
        ) : null}
        {seller.verifiedIdentity ? (
          <Badge variant="neutral" className="gap-1">
            <ShieldCheck className="h-3 w-3" />
            Şəxsiyyət təsdiqlənib
          </Badge>
        ) : null}
        {property.isVerified ? (
          <Badge variant="brand" className="gap-1">
            <Check className="h-3 w-3" />
            Elan təsdiqlənib
          </Badge>
        ) : null}
      </div>

      <p className="mt-3 text-xs text-muted-foreground">
        Üzv: {seller.memberSince} · {seller.activeListings} aktiv elan
      </p>

      <div className="mt-5 space-y-2">
        <Button
          variant={revealed ? "secondary" : "primary"}
          className="w-full"
          onClick={revealPhone}
        >
          <Phone className="h-4 w-4" />
          {revealed ? formatPhoneDisplay(phone) : "Telefonu göstər"}
        </Button>
        <div className="grid grid-cols-2 gap-2">
          <a
            href={whatsappHref}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() =>
              track("WHATSAPP_CLICK", { propertyId: property.id })
            }
            className="inline-flex h-11 items-center justify-center gap-2 rounded-[10px] border border-border bg-surface text-sm font-medium text-foreground/80 transition-colors hover:border-emerald-500/40 hover:text-emerald-700"
          >
            <MessageCircle className="h-4 w-4" />
            WhatsApp
          </a>
          <Button
            variant="secondary"
            onClick={() => {
              track("MESSAGE_CLICK", { propertyId: property.id });
              router.push(`/messages?property=${property.id}`);
            }}
          >
            Mesaj yaz
          </Button>
        </div>
        <Button
          variant="outline"
          className="w-full"
          onClick={() => setViewingOpen(true)}
        >
          <CalendarClock className="h-4 w-4" />
          Baxış təyin et
        </Button>
      </div>

      <p className="mt-4 text-center text-[11px] leading-relaxed text-foreground/40">
        Elan nömrəsi: {property.referenceCode} · {property.views} baxış
      </p>

      <Dialog open={viewingOpen} onOpenChange={setViewingOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Baxış təyin et</DialogTitle>
            <DialogDescription>
              Təklif olunan vaxtlardan birini seçin. Satıcı müraciətinizi təsdiq
              edəcək.
            </DialogDescription>
          </DialogHeader>
          {viewingSent ? (
            <div className="flex flex-col items-center py-8 text-center">
              <span className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                <Check className="h-6 w-6" />
              </span>
              <p className="mt-3 font-medium text-foreground">
                Müraciətiniz göndərildi
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Satıcı təsdiq etdikdən sonra bildiriş alacaqsınız.
              </p>
            </div>
          ) : (
            <div className="mt-2 grid gap-2">
              {["Bu gün 18:00", "Sabah 12:00", "Sabah 16:30", "Cümə 11:00"].map(
                (slot) => (
                  <button
                    key={slot}
                    type="button"
                    onClick={() => setViewingSent(true)}
                    className={cn(
                      "flex items-center justify-between rounded-xl border border-border bg-surface px-4 py-3 text-sm font-medium text-foreground/80 transition-colors hover:border-brand/40 hover:bg-brand-soft/50"
                    )}
                  >
                    {slot}
                    <CalendarClock className="h-4 w-4 text-foreground/40" />
                  </button>
                )
              )}
              <p className="mt-2 flex items-center gap-1.5 text-[11px] text-foreground/40">
                <UserRound className="h-3.5 w-3.5" />
                Demo rejimi — təsdiq bildirişləri API ilə birlikdə gəlir.
              </p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
