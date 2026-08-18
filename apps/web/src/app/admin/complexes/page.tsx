"use client";

import React, { useState } from "react";

interface Complex {
  id: number;
  name: string;
  location: string;
  is_active: boolean;
}

export default function AdminComplexesPage() {
  const [complexes, setComplexes] = useState<Complex[]>([]);

  React.useEffect(() => {
    fetch("/api/admin/complexes", { credentials: "include" })
      .then((r) => r.json())
      .then((d) => setComplexes(d));
  }, []);

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">Residensial Complexlər</h2>
      <div className="card border rounded-xl p-6 mb-6">
        <h3 className="font-semibold mb-4">Yeni Complex</h3>
        <form>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div><label>Complex Name</label><input className="w-full rounded border px-3 py-2" defaultValue="" /></div>
            <div><label>Location</label><input className="w-full rounded border px-3 py-2" defaultValue="" /></div>
          </div>
          <button type="submit" className="w-full rounded border px-3 py-2 text-sm font-medium text-white bg-brand hover:bg-brand/90 mt-4">
            Add Complex
          </button>
        </form>
      </div>
      <div className="overflow-x-auto rounded border bg-surface shadow-sm">
        <table className="w-full min-w-[600px] text-sm">
          <thead>
            <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-foreground/40">
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Location</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {complexes.map((comp) => (
              <tr key={comp.id} className="border-b border-border/40 hover:bg-foreground/[0.02]">
                <td className="px-4 py-3">{comp.name}</td>
                <td className="px-4 py-3">{comp.location || "—"}</td>
                <td className="px-4 py-3">
                  <span className={comp.is_active ? "bg-emerald-500/10 text-emerald-600" : "bg-red-500/10 text-red-600"} px-2 py-1 text-xs font-medium>
                    {comp.is_active ? "Aktiv" : "Deaktiv"}
                  </span>
                </td>
              </tr>
            ))}
            {complexes.length === 0 && (
              <tr>
                <td colSpan={3} className="text-center text-foreground/40 py-8">
                  Complex tapılmadı.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
