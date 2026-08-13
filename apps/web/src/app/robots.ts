import { siteUrl } from "@yenimenzil/config";

export default function robots() {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/admin/", "/profile/", "/messages/", "/add-property/", "/login", "/register", "/api/"],
      },
    ],
    sitemap: `${siteUrl}/sitemap.xml`,
  };
}