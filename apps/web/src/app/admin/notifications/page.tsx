"use client";

import React, { useState, useEffect } from "react";

interface Notif {
  id: number;
  title: string;
  message: string;
}

export default function AdminNotificationsPage() {
  const [notifications, setNotifications] = useState<Notif[]>([]);

  useEffect(() => {
    fetch("/api/admin/notifications", { credentials: "include" })
      .then((r) => r.json())
      .then((d) => setNotifications(d ?? []));
  }, []);

  return (
    <div>
      <h2 className="text-xl font-semibold mb-6">Bildirimler</h2>
      <p>Total: {notifications.length}</p>
      <ul>
        {notifications.map((notif) => {
          return <li key={notif.id}>{notif.title}: {notif.message}</li>;
        })}
      </ul>
    </div>
  );
}
