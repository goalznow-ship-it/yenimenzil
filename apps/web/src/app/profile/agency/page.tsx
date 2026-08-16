"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { MailPlus, ShieldAlert, Trash2, UserPlus } from "lucide-react";
import { Button, Input } from "@yenimenzil/ui";
import { useAuth } from "@/store/auth";
import {
  cancelInvite,
  createInvite,
  inviteRoleLabel,
  inviteStatusLabel,
  isAgencyAdmin,
  listInvites,
  type AgencyInvite
} from "@/services/agency-api";

export default function AgencyToolsPage() {
  const me = useAuth((s) => s.user);
  const router = useRouter();
  const [invites, setInvites] = React.useState<AgencyInvite[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [err, setErr] = React.useState<string | null>(null);
  const [email, setEmail] = React.useState("");
  const [role, setRole] = React.useState<"agent" | "agency_admin">("agent");
  const [submitting, setSubmitting] = React.useState(false);

  const load = React.useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      setInvites(await listInvites());
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xəta");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (!me) return;
    if (!isAgencyAdmin(me.role)) {
      void Promise.resolve().then(() => router.replace("/profile"));
      return;
    }
    void Promise.resolve().then(() => void load());
  }, [me, router, load]);

  if (!me) return null;
  if (!isAgencyAdmin(me.role)) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center text-sm text-muted-foreground">
        <ShieldAlert className="mx-auto mb-3 h-8 w-8 text-amber-500" />
        Bu səhifə yalnız agentlik rəhbərləri üçündür.
      </div>
    );
  }

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setErr(null);
    try {
      await createInvite({ email, role });
      setEmail("");
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xəta");
    } finally {
      setSubmitting(false);
    }
  };

  const revoke = async (id: string) => {
    if (!window.confirm("Dəvəti ləğv etmək istəyirsiniz?")) return;
    try {
      await cancelInvite(id);
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xəta");
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-xl font-bold text-foreground">Komanda dəvətləri</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Agentlik üzvlərini email üzərindən dəvət edin. Dəvət qəbul edən şəxs
        agentliyə qoşulur və elanlarınızı idarə edə bilər.
      </p>

      <form
        onSubmit={submit}
        className="mt-6 flex flex-col gap-3 rounded-2xl border border-border/70 bg-surface p-4 sm:flex-row sm:items-end"
      >
        <label className="flex-1">
          <span className="mb-1 block text-xs font-semibold text-foreground">
            Email
          </span>
          <Input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="agent@example.az"
          />
        </label>
        <label className="sm:w-44">
          <span className="mb-1 block text-xs font-semibold text-foreground">
            Rol
          </span>
          <select
            value={role}
            onChange={(e) =>
              setRole(e.target.value as "agent" | "agency_admin")
            }
            className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm"
          >
            <option value="agent">Agent</option>
            <option value="agency_admin">Rəhbər</option>
          </select>
        </label>
        <Button type="submit" disabled={submitting}>
          <UserPlus className="mr-2 h-4 w-4" />
          {submitting ? "Göndərilir…" : "Dəvət et"}
        </Button>
      </form>

      {err && (
        <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">
          {err}
        </p>
      )}

      <div className="mt-6 overflow-hidden rounded-2xl border border-border/70 bg-surface">
        {loading ? (
          <div className="p-6 text-center text-sm text-muted-foreground">
            Yüklənir…
          </div>
        ) : invites.length === 0 ? (
          <div className="p-6 text-center text-sm text-muted-foreground">
            <MailPlus className="mx-auto mb-2 h-6 w-6 opacity-50" />
            Hələ dəvət göndərilməyib.
          </div>
        ) : (
          <ul className="divide-y divide-border/70">
            {invites.map((invite) => (
              <li
                key={invite.id}
                className="flex items-center justify-between gap-3 px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {invite.email}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {inviteRoleLabel(invite.role)} ·{" "}
                    {inviteStatusLabel(invite.status)} ·{" "}
                    {new Date(invite.expires_at).toLocaleDateString("az-AZ")}
                  </p>
                </div>
                {invite.status === "pending" && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => revoke(invite.id)}
                    aria-label="Dəvəti ləğv et"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}