"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { Tabs, TabsList, TabsTrigger } from "@yenimenzil/ui";
import { LayoutDashboard, Building2, Bell, MessageSquare, Wallet, Search } from "lucide-react";
import { RequireAuth } from "@/components/auth/auth-provider";
import { OverviewTab } from "./overview-tab";
import { MyListingsTab } from "./my-listings-tab";
import { SavedSearchesTab } from "./saved-searches-tab";
import { NotificationsTab } from "./notifications-tab";
import { MessagesTab } from "./messages-tab";
import { WalletTab } from "./wallet-tab";

type DashboardTab = "overview" | "listings" | "searches" | "notifications" | "messages" | "wallet";

const VALID_TABS: DashboardTab[] = [
  "overview",
  "listings",
  "searches",
  "notifications",
  "messages",
  "wallet"
];

export function DashboardPage() {
  const searchParams = useSearchParams();
  const requested = searchParams.get("tab") as DashboardTab | null;
  const initialTab =
    requested && VALID_TABS.includes(requested) ? requested : "overview";
  const [tab, setTab] = React.useState<DashboardTab>(initialTab);

  return (
    <RequireAuth>
      <div className="mx-auto w-full max-w-5xl px-4 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">İdarə paneli</h1>
            <p className="mt-0.5 text-sm text-muted-foreground">
              Elanlarınızı, axtarışlarınızı və hesabınızı buradan idarə edin.
            </p>
          </div>
          <a
            href="/add-property"
            className="inline-flex items-center gap-2 rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-brand/25 transition-colors hover:bg-brand/90"
          >
            <Building2 className="h-4 w-4" />
            Yeni elan
          </a>
        </div>

        <Tabs value={tab} onValueChange={(v) => setTab(v as DashboardTab)} className="mt-6">
          <div className="overflow-x-auto pb-1">
            <TabsList>
              <TabsTrigger value="overview">
                <LayoutDashboard className="mr-1.5 h-4 w-4" />
                Ümumi
              </TabsTrigger>
              <TabsTrigger value="listings">
                <Building2 className="mr-1.5 h-4 w-4" />
                Elanlarım
              </TabsTrigger>
              <TabsTrigger value="searches">
                <Search className="mr-1.5 h-4 w-4" />
                Saxlanılmış axtarışlar
              </TabsTrigger>
              <TabsTrigger value="messages">
                <MessageSquare className="mr-1.5 h-4 w-4" />
                Mesajlar
              </TabsTrigger>
              <TabsTrigger value="notifications">
                <Bell className="mr-1.5 h-4 w-4" />
                Bildirişlər
              </TabsTrigger>
              <TabsTrigger value="wallet">
                <Wallet className="mr-1.5 h-4 w-4" />
                Balans
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="mt-6">
            {tab === "overview" ? <OverviewTab /> : null}
            {tab === "listings" ? <MyListingsTab /> : null}
            {tab === "searches" ? <SavedSearchesTab /> : null}
            {tab === "messages" ? <MessagesTab /> : null}
            {tab === "notifications" ? <NotificationsTab /> : null}
            {tab === "wallet" ? <WalletTab /> : null}
          </div>
        </Tabs>

        <div className="mt-10 flex flex-wrap gap-x-6 gap-y-2 border-t border-border/70 pt-5 text-[13px] text-muted-foreground">
          <a href="/profile/edit" className="transition-colors hover:text-brand">
            Profil məlumatları
          </a>
          <a href="/profile/analytics" className="transition-colors hover:text-brand">
            Satış statistikası
          </a>
        </div>
      </div>
    </RequireAuth>
  );
}
