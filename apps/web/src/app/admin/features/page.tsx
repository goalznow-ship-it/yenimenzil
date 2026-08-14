"use client";

import * as React from "react";
import { Search, Plus } from "lucide-react";
import { Button, Input } from "@yenimenzil/ui";
import { adminApi, type FeatureRow } from "@/services/admin-api";
import { AdminPageHeader } from "../layout";

export default function AdminFeaturesPage() {
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [data, setData] = React.useState<FeatureRow[]>([]);
  const [pagination, setPagination] = React.useState({ page: 1, pages: 1, total: 0, limit: 100 });
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [updating, setUpdating] = React.useState<Record<string, boolean>>({});
  const [editLabel, setEditLabel] = React.useState<Record<string, string>>({});
  const [creating, setCreating] = React.useState(false);
  const [createCode, setCreateCode] = React.useState("");
  const [createLabel, setCreateLabel] = React.useState("");
  const isMountedRef = React.useRef(false);

   const load = React.useCallback(async () => {
    if (isMountedRef.current) {
      setLoading(true);
      setError(null);
      try {
        const res = await adminApi.features({
          page,
          search: search || undefined
        });
        setData(res.data);
        setPagination(res.pagination);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Xəta");
      } finally {
        setLoading(false);
      }
    }
  }, [page, search]);

  React.useEffect(() => {
    isMountedRef.current = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
    return () => {
      isMountedRef.current = false;
    };
  }, [load]);

  const createFeature = async () => {
    if (!createCode || !createLabel) return;
    setCreating(true);
    try {
      await adminApi.featureCreate({ code: createCode, label_az: createLabel });
      setCreating(false);
      setCreateCode("");
      setCreateLabel("");
      await load();
    } catch (err) {
      setCreating(false);
      window.alert(err instanceof Error ? err.message : "Xəta");
    }
  };

  const updateFeature = async (id: string, label_az: string) => {
    if (!label_az) return;
    setUpdating(prev => ({ ...prev, [id]: true }));
    try {
      await adminApi.featureUpdate(id, { label_az });
      setUpdating(prev => ({ ...prev, [id]: false }));
      await load();
    } catch (err) {
      setUpdating(prev => ({ ...prev, [id]: false }));
      window.alert(err instanceof Error ? err.message : "Xəta");
    }
  };

  const deleteFeature = async (id: string) => {
    if (!window.confirm("Feature'i silmək istədiyinizdən əminsiniz?")) return;
    try {
      await adminApi.featureDelete(id);
      await load();
    } catch (err) {
      window.alert(err instanceof Error ? err.message : "Xəta");
    }
  };

  return (
    <div>
      <AdminPageHeader title="Xüsusiyyət katalogu" subtitle="Elan xüsusiyyətlərini idarə edin" icon={Search} />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="relative min-w-52">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/40" />
          <Input
            className="pl-9"
            placeholder="Axtar..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                setPage(1);
              }
            }}
          />
        </div>
        <Button onClick={() => setPage(1)} size="sm">
          Yenilə
        </Button>
      </div>

      {error ? <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{error}</p> : null}

      <div className="mb-4">
        <Button
          variant="secondary"
          onClick={() => setCreating(true)}
        >
          <Plus className="h-3.5 w-3.5" /> Yeni xüsusiyyət əlavə et
        </Button>
      </div>

      {creating && (
        <div className="mt-4 rounded-2xl border border-border/60 bg-surface p-4">
          <h3 className="mb-2 font-medium">Yeni xüsusiyyət əlavə et</h3>
          <form onClick={(e) => e.preventDefault()} className="space-y-3">
            <div>
              <Input
                value={createCode}
                onChange={(e) => setCreateCode(e.target.value)}
                placeholder="Kod (məsələn: elevator)"
                required
              />
            </div>
            <div>
              <Input
                value={createLabel}
                onChange={(e) => setCreateLabel(e.target.value)}
                placeholder="Label (AZ) (məsələn: Asansor)"
                required
              />
            </div>
            <div className="flex justify-end">
              <Button onClick={createFeature} size="sm">
                Yarat
              </Button>
              <Button
                onClick={() => setCreating(false)}
                size="sm"
                variant="secondary"
              >
                İmtina et
              </Button>
            </div>
          </form>
        </div>
      )}

      <div className="overflow-x-auto rounded-2xl border border-border/60 bg-surface shadow-sm">
        <table className="w-full min-w-[600px] text-sm">
          <thead>
            <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-foreground/40">
              <th className="px-4 py-3">Kod</th>
              <th className="px-4 py-3">Label (AZ)</th>
              <th className="px-4 py-3">Yaradılma tarixi</th>
              <th className="px-4 py-3">Əməliyyatlar</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-foreground/40">
                  Yüklənir...
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-foreground/40">
                  Xüsusiyyət tapılmadı
                </td>
              </tr>
            ) : (
              data.map((feature) => (
                <tr key={feature.id} className="border-b border-border/40 hover:bg-foreground/[0.02]">
                  <td className="px-4 py-3">{feature.code}</td>
                  <td className="px-4 py-3">{feature.label_az}</td>
                  <td className="px-4 py-3 text-xs text-foreground/50">
                    {feature.created_at ? feature.created_at.slice(0, 10) : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {creating ? (
                      <Button size="sm" variant="secondary" disabled>
                        Yaratılır...
                      </Button>
                    ) : updating[feature.id] ? (
                      <form onClick={(e) => e.preventDefault()} className="flex gap-2">
                        <Input
                          value={editLabel[feature.id] ?? feature.label_az}
                          onChange={(e) =>
                            setEditLabel(prev => ({ ...prev, [feature.id]: e.target.value }))
                          }
                          className="flex-1"
                          placeholder="Label AZ"
                        />
                        <Button
                          onClick={() =>
                            updateFeature(
                              feature.id,
                              editLabel[feature.id] ?? feature.label_az
                            )
                          }
                          size="sm"
                        >
                          Yadda saxla
                        </Button>
                        <Button
                          onClick={() => {
                            setUpdating(prev => ({ ...prev, [feature.id]: false }));
                            setEditLabel(prev => {
                              const next = { ...prev };
                              delete next[feature.id];
                              return next;
                            });
                          }}
                          size="sm"
                          variant="secondary"
                        >
                          İmtina et
                        </Button>
                      </form>
                    ) : (
                      <>
                        <Button
                          onClick={() => {
                            setEditLabel(prev => ({
                              ...prev,
                              [feature.id]: feature.label_az
                            }));
                            setUpdating(prev => ({ ...prev, [feature.id]: true }));
                          }}
                          size="sm"
                          variant="secondary"
                        >
                          Düzelət
                        </Button>
                        <Button
                          onClick={() => deleteFeature(feature.id)}
                          size="sm"
                          variant="secondary"
                        >
                          Sil
                        </Button>
                      </>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pagination.pages > 1 ? (
        <div className="mt-4 flex items-center justify-between text-sm text-foreground/50">
          <span>
            {pagination.total} nəticə, {pagination.pages} səhifə
          </span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="secondary"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Əvvəlki
            </Button>
            <Button
              size="sm"
              variant="secondary"
              disabled={page >= pagination.pages}
              onClick={() => setPage((p) => p + 1)}
            >
              Növbəti
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}