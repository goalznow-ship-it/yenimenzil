"use client";

import React from "react";
import { useState } from "react";

export default function AdminSettingsPage() {
  const [maintenanceMode, setMaintenanceMode] = useState(false);
  const [supportEmail, setSupportEmail] = useState("");
  const [supportPhone, setSupportPhone] = useState("");
  const [twitter, setTwitter] = useState("");
  const [facebook, setFacebook] = useState("");
  const [linkedin, setLinkedin] = useState("");
  const [instagram, setInstagram] = useState("");

  React.useEffect(() => {
    fetch("/api/admin/settings", { credentials: "include" })
      .then((r) => r.json())
      .then((d) => {
        setMaintenanceMode(d.maintenance_mode ?? false);
        setSupportEmail(d.support_email ?? "");
        setSupportPhone(d.support_phone ?? "");
        setTwitter(d.twitter ?? "");
        setFacebook(d.facebook ?? "");
        setLinkedin(d.linkedin ?? "");
        setInstagram(d.instagram ?? "");
      });
  }, []);

  const handleSave = () => {
    fetch("/api/admin/settings", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        maintenance_mode: maintenanceMode,
        support_email: supportEmail,
        support_phone: supportPhone,
        twitter,
        facebook,
        linkedin,
        instagram
      })
    });
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">Platform Ayarları</h2>
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div>
          <h4 className="font-semibold mb-3">Çalışma Modu</h4>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={maintenanceMode}
              onChange={e => setMaintenanceMode(e.target.checked)}
              className="rounded border px-2 py-1"
            />
            <span>Aktif</span>
          </label>
        </div>
        <div>
          <h4 className="font-semibold mb-3">Destek E-postası</h4>
          <input
            type="email"
            value={supportEmail}
            onChange={e => setSupportEmail(e.target.value)}
            className="w-full rounded border px-3 py-2 text-sm"
            placeholder="support@idealev.az"
          />
        </div>
      </div>
      <div>
        <h4 className="font-semibold mb-3">Telefon</h4>
        <input
          type="tel"
          value={supportPhone}
          onChange={e => setSupportPhone(e.target.value)}
          className="w-full rounded border px-3 py-2 text-sm"
          placeholder="+994 12 345 67 89"
        />
      </div>
      <div>
        <h4 className="font-semibold mb-3">Sosyal Linkler</h4>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label>Twitter</label>
            <input
              value={twitter}
              onChange={e => setTwitter(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm"
              placeholder="twitter.com/idealev"
            />
          </div>
          <div>
            <label>Facebook</label>
            <input
              value={facebook}
              onChange={e => setFacebook(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm"
              placeholder="facebook.com/idealev"
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label>LinkedIn</label>
            <input
              value={linkedin}
              onChange={e => setLinkedin(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm"
              placeholder="linkedin.com/company/idealev"
            />
          </div>
          <div>
            <label>Instagram</label>
            <input
              value={instagram}
              onChange={e => setInstagram(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm"
              placeholder="instagram.com/idealev"
            />
          </div>
        </div>
      </div>
      <button onClick={handleSave} className="w-full rounded border px-3 py-2 text-sm font-medium text-white bg-brand hover:bg-brand/90 mt-6">Ayarları Kaydet</button>
    </div>
  );
}
