# YeniMenzil.az — Design System

## 1. Brand

- Name: **YeniMenzil.az**
- Slogan: *Yeni məkanını burada tap.*
- Tone: premium, calm, trustworthy, image-first, location-first.

## 2. Color tokens

| Token | Value | Usage |
|---|---|---|
| `background` | `#F7F8F6` | App background |
| `surface` | `#FFFFFF` | Cards, panels |
| `foreground` | `#141716` | Primary text |
| `muted-foreground` | `#666D69` | Secondary text |
| `border` | `#E5E8E5` | Hairline borders |
| `brand` | `#15543F` | Deep premium green (sparingly) |
| `brand-hover` | `#103F30` | Brand hover |
| `brand-soft` | `#EDF5F1` | Soft brand background |
| `accent` | `#C7A45A` | Gold — premium/VIP contexts only |
| `warning` | amber | Warnings |
| `error` | red | Errors |
| `success` | green | Success |

The interface stays mostly neutral. Green is a deliberate accent, gold is
reserved for premium/VIP.

## 3. Typography

- Font: **Geist** (Sans for UI, Mono for codes/price-free numeric contexts).
- Sizes: 12/14/16/18/20/24/30/36/48/60 scale.
- Numeric prices use tabular figures for stable alignment.

## 4. Radius & shadows

- Buttons: 10–12px · Cards: 14–18px · Dialogs: 18–24px
- Property images: 4:3 aspect ratio.
- Shadows: very subtle (`shadow-sm` only); prefer whitespace over borders.

## 5. Components

Primitives (packages/ui): Button, Input, Select, Combobox, SearchInput, Modal,
Drawer, BottomSheet, Tabs, Badge, Avatar, Tooltip, Skeleton, EmptyState,
ErrorState, Pagination, Breadcrumb, Toast.

Composite: Header, Footer, MobileNav, PropertyCard, PropertyGallery,
SearchBar, FilterBar, FilterSheet, ResultMap, PriceAnalysisCard,
ContactCard, SectionHeading, PropertyGrid.

## 6. Motion

Subtle only: heart interaction, filter selection, modal/drawer transitions,
gallery transition, toasts. No dramatic effects, no glassmorphism excess, no
gradient soup. Property card hover: tiny image zoom + slight elevation.

## 7. Content rules

- Azerbaijani is primary UI language; en/ru supported.
- Price formats: `245 000 ₼` · `1 200 ₼ / ay` · `250 ₼ / gün` · `2 579 ₼ / m²`.
- Paid placements are always labelled ("Önə çıxarılıb" / "Reklam").
- Estimates (price analysis) are always labelled as estimates.
