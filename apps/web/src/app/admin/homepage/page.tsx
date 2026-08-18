"use client";

import React from "react";
import { useState } from "react";

export default function AdminHomepagePage() {
  const [heroContent, setHeroContent] = useState<string>("");
  const [promoBanners, setPromoBanners] = useState<string[]>([]);
  const [announcementBanner, setAnnouncementBanner] = useState<string>("");

  React.useEffect(() => {
    fetch("/api/admin/homepage", { credentials: "include" })
      .then((r) => r.json())
      .then((d) => {
        setHeroContent(d.hero_content || "");
        setPromoBanners(d.promo_banners || []);
        setAnnouncementBanner(d.announcement_banner || "");
      });
  }, []);

  const handleHero = (e: React.ChangeEvent<HTMLTextAreaElement>) => setHeroContent(e.target.value);
  const handlePromo = (e: React.ChangeEvent<HTMLTextAreaElement>) => setPromoBanners(e.target.value.split(","));
  const handleAnnounce = (e: React.ChangeEvent<HTMLTextAreaElement>) => setAnnouncementBanner(e.target.value);

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">Ana Sayfa İçeriği</h2>
      <div className="card border rounded-xl p-6 mb-6">
        <h3 className="font-semibold mb-4">Hero İçeriği</h3>
        <textarea value={heroContent} onChange={handleHero} defaultValue={heroContent} />
      </div>
      <div className="card border rounded-xl p-6 mb-6">
        <h3 className="font-semibold mb-4">Promo Bannerlar</h3>
        <textarea value={promoBanners.join(",")} onChange={handlePromo} defaultValue={promoBanners.join(",")} />
      </div>
      <div className="card border rounded-xl p-6">
        <h3 className="font-semibold mb-4">Duyuru Bannerı</h3>
        <textarea value={announcementBanner} onChange={handleAnnounce} defaultValue={announcementBanner} />
      </div>
    </div>
  );
}
