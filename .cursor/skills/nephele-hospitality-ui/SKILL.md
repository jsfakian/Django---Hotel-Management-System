---
name: nephele-hospitality-ui
description: Nephele hospitality UI/UX rules — Aegean brand, guest stay journey vs dense ops tools. Use when designing or changing React/MUI frontend pages for landing, auth, guest portal, or staff shell.
---

# Nephele Hospitality UI

Pair with **ui-ux-pro-max** using industry keywords: Hotel, hospitality, Mediterranean service, booking.

## Dual surfaces

| Surface | Audience | UX mode |
|---------|----------|---------|
| Public | Prospects, guests signing in | Brand-first, place atmosphere, calm CTAs |
| Guest portal | Authenticated guests | Stay journey (arrive → stay → invoice), not CRUD |
| Ops | Admin, manager, receptionist, staff | Dense tools, clear hierarchy, no marketing heroes |

Never restyle ops dashboards into landing-page layouts.

## Brand tokens (Aegean)

- Primary: deep sea teal `#0B5F6B`
- Primary dark: `#084852`
- Secondary / sand: `#C4A574`
- Background: warm off-white `#F7F4EF`
- Paper: `#FFFcf8`
- Text: `#1A2426`
- Display font: Fraunces (serif)
- UI font: Source Sans 3 (sans) — never Roboto, Inter, Arial, or system-ui alone

Forbidden: purple/indigo gradients, terracotta-on-cream AI cliché, broadsheet hairline newspaper layouts, glow stacks, emoji as decoration.

## Public / marketing rules

- First viewport: brand name dominant, one headline, one short sentence, one CTA group, one full-bleed place image.
- No feature cards, stats, or promo chips in the hero.
- No detached badges overlaid on hero media.
- Prefer real hospitality photography (coast, lobby light, terrace) over abstract gradients as the main idea.

## Guest portal rules

- Upcoming stay is the hero of the dashboard.
- Prefer journey cards and timelines over dense DataTables.
- Status language is human (Confirmed, Checked in) not raw enums alone.
- Privacy/GDPR pages stay calm and clear.

## Ops rules

- Keep information density; improve grouping and empty states.
- Sidebar groups: Front desk, Revenue, Property (where applicable).
- Sticky page headers for list/detail/form consistency.
- Empty states explain next action in one sentence + one CTA.

## Acceptance checks

- Brand still readable if nav text is removed from the landing hero.
- Guest pages do not feel like admin CRUD.
- Ops pages remain scannable without large marketing blocks.
- Focus rings visible; contrast meets WCAG AA for body text and primary buttons.
