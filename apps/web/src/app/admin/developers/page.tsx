"use client";

import React, { useState } from "react";

interface Developer {
  id: number;
  name: string;
  contact: string;
  is_active: boolean;
}

export default function AdminDevelopersPage() {
  const [developers, setDevelopers] = useState<Developer[]>([]);

  React.useEffect(() => {
    fetch("/api/admin/developers", { credentials: "include" })
      .then((r) => r.json())
      .then((d) => setDevelopers(d));
  }, []);

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">Developerlar</h2>
      <div className="card border rounded-xl p-6 mb-6">
        <h3 className="font-semibold mb-4">Yeni Developer</h3>
        <form>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div><label>Name</label><input className="w-full rounded border px-3 py-2" defaultValue="" /></div>
            <div><label>Contact</label><input className="w-full rounded border px-3 py-2" defaultValue="" /></div>
          </div>
          <button type="submit" className="w-full rounded border px-3 py-2 text-sm font-medium text-white bg-brand hover:bg-brand/90 mt-4">
            Add Developer
          </button>
        </form>
      </div>
      <div className="overflow-x-auto rounded border bg-surface shadow-sm">
        <table className="w-full min-w-[600px] text-sm">
          <thead>
            <tr className="border-b border-border/60 text-left text-xs uppercase tracking-wider text-foreground/40">
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Contact</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {developers.map((dev) => (
              <tr key={dev.id} className="border-b border-border/40 hover:bg-foreground/[0.02]">
                <td className="px-4 py-3">{dev.name}</td>
                <td className="px-4 py-3">{dev.contact || "—"}</td>
                <td className="px-4 py-3">
                  <span className={dev.is_active ? "bg-emerald-500/10 text-emerald-600" : "bg-red-500/10 text-red-600"} px-2 py-1 text-xs font-medium>
                    {dev.is_active ? "Aktiv" : "Deaktiv"}
                  </span>
                </td>
              </tr>
            ))}
            {developers.length === 0 && (
              <tr>
                <td colSpan={3} className="text-center text-foreground/40 py-8">
                  Developer tapılmadı.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
