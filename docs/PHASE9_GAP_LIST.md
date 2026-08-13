# Phase 9: Marketplace/Product Completeness Gap List

## Audit Date: 2026-08-13
## Base: Phase 8 complete (commit c2ddf0f)

---

## ✅ What's Already Implemented (Phases 1-8)

### Core Marketplace
- [x] Search with filters (deal, district, property type, rooms, price, area, metro, building type, repair, owner/verified only)
- [x] Search view modes: List, Grid, Map (with markers, bounds search)
- [x] Property detail: gallery, summary, description, features, price analysis, price history, area intelligence, similar listings
- [x] Property listing wizard (multi-step, validation, media upload)
- [x] Favorites (heart icon, local store + API sync)
- [x] User profile (name, phone, city, bio)
- [x] Map exploration (markers, bounds search, filters sidebar, selected listing panel)
- [x] Admin panel (listings, agencies, agents, users, reports, dashboard, audit, catalog, intelligence, promotions)
- [x] Property components: card, gallery, price analysis, price history, area intelligence, badges, contact card
- [x] Search filters with many options (deal, district, property type, rooms, price, area, metro, building type, repair, owner/verified)
- [x] JSON-LD Product schema + Open Graph metadata on property pages
- [x] Auth with JWT httpOnly cookies, roles (user, moderator, admin, super_admin)
- [x] Rate limiting, security headers, structured logging
- [x] Docker production stack with Nginx, Postgres, Redis, MinIO

---

## 🔴 CRITICAL Gaps (Must Have for Production Launch)

### 1. SEO & Discovery (Week 1)
- [ ] **sitemap.xml generation** (static + dynamic for properties)
- [ ] **robots.txt**
- [ ] **RealEstateListing JSON-LD schema** (schema.org/RealEstateListing) on property pages
- [ ] **BreadcrumbList JSON-LD** on property pages
- [ ] Canonical URLs for search/filter pages
- [ ] Multi-language hreflang (az_AZ, en, ru) if needed
- [ ] Search result pagination SEO (rel=next/prev or proper canonical)

### 2. User Dashboard & Account (Week 1-2)
- [ ] **"My Listings" tab** (create, edit, archive, relist, delete, promote)
- [ ] **"My Favorites" with folders/collections**
- [ ] **"Saved Searches" with email/push alerts**
- [ ] **"Recently Viewed"** section
- [ ] **"Messages/Inbox"** (real implementation, not placeholder)
- [ ] **"Notifications Center"** (bell icon, real-time)
- [ ] **"Wallet" page** (balance, top-up, transactions)
- [ ] **"Promotions" management** (buy, activate, view performance)
- [ ] **Email/notification preferences** management
- [ ] **2FA/MFA setup** for users (not just admin)

### 3. Messages & Communication (Week 2)
- [ ] **Real-time messaging** (WebSocket/SSE)
- [ ] **Conversation list** with unread counts
- [ ] **Message threading** per listing
- [ ] **Push/email notifications** for new messages
- [ ] **Attachments** (images, documents)
- [ ] **"Contact agent" form** on property page (pre-filled)

---

## 🟠 HIGH VALUE Gaps (Should Have)

### 4. Listing Detail UX Enhancements (Week 2-3)
- [ ] **360° tour / video support** in gallery
- [ ] **Download PDF brochure** (generate on-the-fly)
- [ ] **Share via WhatsApp/Telegram/X/Email** (native share API)
- [ ] **Schedule viewing inline** (calendar picker)
- [ ] **Mortgage calculator inline** (interactive)
- [ ] **Report listing** flow (modal with reasons)
- [ ] **"Save search from this listing"** button
- [ ] **Similar listings** on search results (not just detail)
- [ ] **Nearby amenities** (schools, transport, shops) on detail page

### 5. Search & Filters Advanced (Week 3)
- [ ] **Price per m² sort** (asc/desc)
- [ ] **Promoted-first sort** option
- [ ] **"With video tour" filter**
- [ ] **"Furnished" filter**
- [ ] **Construction year range** slider
- [ ] **Floor range** slider
- [ ] **Document type** filter
- [ ] **Seller kind** filter (owner/agency/agent)
- [ ] **Keyword search** in description/title
- [ ] **"With video tour" filter**
- [ ] **"Has virtual tour" filter**
- [ ] **Saved search → email alert** (cron job)

### 6. Map & Geospatial (Week 3-4)
- [ ] **"List follows map"** toggle (sync list to map viewport)
- [ ] **Marker clustering** for high density
- [ ] **Heat map** toggle
- [ ] **Polygon/rectangle search** (draw on map)
- [ ] **"Draw radius" search** (center + radius km)
- [ ] **Nearby amenities overlay** (schools, metro, shops, hospitals)
- [ ] **Commute time** (isochrone) from workplace
- [ ] **Cluster markers** for high density

### 7. Favorites & Comparison (Week 3)
- [ ] **Favorites folders/collections** (rename, reorder, share)
- [ ] **Saved searches with email/push alerts**
- [ ] **Comparison feature** (side-by-side up to 4 properties)
- [ ] **Recently viewed** (auto-tracked, 20 items)

---

## 🟡 MEDIUM VALUE Gaps (Nice to Have)

### 8. Seller/Agent/Agency Experience (Week 4-5)
- [ ] **Agent public profile** page (/agent/:id)
- [ ] **Agency public profile** page (/agency/:id)
- [ ] **Seller analytics dashboard** (views, favorites, inquiries, conversion)
- [ ] **Promote listing** UI (select tier, duration, pay from wallet/card)
- [ ] **Relist/renew** expired listings
- [ ] **Bulk actions** for agencies (CSV import, bulk promote)
- [ ] **Agency dashboard** (team performance, listings overview)

### 9. Notifications & Real-time (Week 4)
- [ ] **In-app notification center** (bell icon)
- [ ] **Real-time updates** (SSE/WebSocket) for messages, favorites, views
- [ ] **Email digest** (daily/weekly new matches for saved searches)
- [ ] **Push notifications** (Web Push API)
- [ ] **Notification preferences** granular (email/push per event type)

### 10. Promotion & Payment UX (Week 4-5)
- [ ] **Promotion purchase flow** (tier selection → duration → payment)
- [ ] **Wallet top-up UI** (card, Apple/Google Pay, bank transfer)
- [ ] **Payment history** with invoices/receipts (PDF)
- [ ] **Auto-renew** for promotions
- [ ] **Promotion performance** tracking (views, clicks, CTR)

### 11. SEO & Structured Data (Week 1-2)
- [ ] **RealEstateListing JSON-LD** (schema.org/RealEstateListing)
- [ ] **BreadcrumbList JSON-LD** on all pages
- [ ] **Canonical URLs** for search/filter pages
- [ ] **Sitemap.xml** (static + dynamic property URLs)
- [ ] **robots.txt**
- [ ] **hreflang** for multi-language

### 12. Mobile/Responsive Polish (Week 2)
- [ ] Touch-friendly map controls
- [ ] Bottom sheet animations (smooth)
- [ ] Safe area insets (notch/Dynamic Island)
- [ ] Pull-to-refresh on lists
- [ ] Swipe gestures (swipe to favorite, swipe to delete)

---

## 🟢 POLISH Gaps (Production Quality)

### 13. Empty/Loading/Error States (Week 1-2)
- [ ] Consistent **Skeleton** patterns everywhere
- [ ] **Error boundaries** per page section
- [ ] **Global 500/503** page with retry
- [ ] **Offline** detection + banner
- [ ] **Retry** buttons on failed fetches
- [ ] **Empty state** illustrations for all sections

### 14. Accessibility (Week 2-3)
- [ ] ARIA labels on map controls
- [ ] Focus management in modals/sheets
- [ ] Color contrast verification (WCAG AA)
- [ ] Keyboard navigation for map
- [ ] Screen reader announcements for dynamic content
- [ ] Focus trap in modals/sheets

### 15. Performance & Images (Week 2)
- [ ] Next.js **Image optimization** for external images (loader)
- [ ] **Blur placeholders** (LQIP)
- [ ] **AVIF/WebP** automatic conversion
- [ ] **Lazy loading** optimization (priority, sizes)
- [ ] **Preload** critical images (hero)
- [ ] **Font optimization** (subset, preload)

### 16. Admin Operational Gaps (Week 3-4)
- [ ] **Bulk export** (CSV/Excel) for listings, users, agencies
- [ ] **"Impersonate user"** for support
- [ ] **Content moderation queue** with AI spam hints
- [ ] **Automated spam detection** (rules + ML)
- [ ] **Audit log** search/export
- [ ] **Feature flags** management

### 17. Production Infrastructure (Week 1-2)
- [ ] **Cookie consent banner** (GDPR)
- [ ] **Maintenance mode** toggle
- [ ] **Feature flags** system
- [ ] **Error tracking** (Sentry integration)
- [ ] **Analytics** (GA4 + custom events)
- [ ] **Performance monitoring** (Web Vitals)
- [ ] **Uptime monitoring** (health endpoints)

---

## Summary

| Priority | Count | Est. Effort |
|----------|-------|-------------|
| 🔴 Critical | 10 | 2-3 weeks |
| 🟠 High | 18 | 3-4 weeks |
| 🟡 Medium | 15 | 3-4 weeks |
| 🟢 Polish | 15 | 2-3 weeks |
| **Total** | **58 items** | **10-14 weeks** |

---

## Recommended Sprint Order

### Sprint 1 (Week 1): SEO & Foundation
1. sitemap.xml + robots.txt
2. RealEstateListing JSON-LD + BreadcrumbList
3. Global error boundaries + 500 page
4. Error boundaries per section

### Sprint 2 (Week 2): User Dashboard Core
1. My Listings tab (CRUD)
2. My Favorites with folders
2. Saved Searches + email alerts (cron)
3. Recently viewed
4. Error boundaries + skeletons everywhere

### Sprint 3 (Week 3): Messages & Dashboard Complete
1. Messages (WebSocket + UI)
2. Notifications center
3. Wallet page + top-up
4. Promotions management
4. Notifications preferences

### Sprint 4 (Week 4): Search & Map Advanced
1. Advanced filters (all missing)
2. Map clustering + heat map + polygon search
3. Saved searches + email alerts
4. Comparison feature
4. Recently viewed

### Sprint 5 (Week 5): Seller/Agency + Promotions
1. Agent/Agency public profiles
2. Seller analytics dashboard
3. Promotion purchase flow
4. Wallet top-up + payment history
5. Promotion performance tracking

### Sprint 6 (Week 6): Polish & Accessibility
1. Sitemap.xml + robots.txt (if not done)
2. Accessibility audit + fixes
3. Mobile gestures + safe areas
4. Performance images (LQIP, AVIF, lazy)
5. Cookie consent + maintenance mode
6. Error tracking (Sentry) + analytics

---

## Dependencies

- **Backend API extensions needed** for: saved searches, notifications, messages (WebSocket), wallet, promotions, seller analytics, comparison
- **Database migrations** for: saved_searches, notifications, messages, wallet_transactions, promotion_orders, comparison_sessions
- **Background jobs** for: email alerts, sitemap generation, promotion expiry, analytics aggregation
- **External services**: Sentry, email provider (SendGrid/Postmark), push provider (Web Push), payment provider (Stripe)