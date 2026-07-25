---
name: Ivory Protocol
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#434652'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#737783'
  outline-variant: '#c3c6d4'
  surface-tint: '#2b5bb5'
  primary: '#003178'
  on-primary: '#ffffff'
  primary-container: '#0d47a1'
  on-primary-container: '#a1bbff'
  inverse-primary: '#b0c6ff'
  secondary: '#0058bb'
  on-secondary: '#ffffff'
  secondary-container: '#1471e6'
  on-secondary-container: '#fefcff'
  tertiary: '#602100'
  on-tertiary: '#ffffff'
  tertiary-container: '#853100'
  on-tertiary-container: '#ffa781'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d9e2ff'
  primary-fixed-dim: '#b0c6ff'
  on-primary-fixed: '#001945'
  on-primary-fixed-variant: '#00429c'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc7ff'
  on-secondary-fixed: '#001a41'
  on-secondary-fixed-variant: '#004493'
  tertiary-fixed: '#ffdbcd'
  tertiary-fixed-dim: '#ffb596'
  on-tertiary-fixed: '#360f00'
  on-tertiary-fixed-variant: '#7d2d00'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  headline-xl:
    fontFamily: Hanken Grotesk
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  xxl: 64px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
---

## Brand & Style
The design system is engineered for institutional trust and sophisticated financial clarity. It targets a professional audience that values precision and reliability over decorative trends. The aesthetic direction is **Corporate / Modern** with a focus on **Tonal Minimalism**.

The UI evokes an emotional response of security and "quiet confidence" through the use of expansive white space, meticulous alignment, and a reduction of visual noise. By favoring soft depth over hard borders, the system achieves a state of "digital architecture" where hierarchy is communicated through subtle elevation and typographic weight rather than heavy graphic elements.

## Colors
The palette is built on a foundation of "High-Value White." The primary interaction color is a deep, authoritative Blue (#0D47A1), used for critical actions and brand markers. A secondary, more vibrant Blue (#1A73E8) is reserved for focus states and secondary links to maintain a dynamic yet professional range.

Surfaces follow a strict hierarchy: 
- **Base Surface:** #FFFFFF for primary content areas and page backgrounds.
- **Subtle Containers:** #F8F9FA used to group related information or define sidebars without creating visual friction.
- **Contrast Text:** A near-black (#121212) ensures maximum accessibility against white backgrounds, while a medium gray (#4A4A4A) provides balanced hierarchy for metadata and secondary descriptions.

## Typography
This design system utilizes **Hanken Grotesk** across all roles to maintain a unified, contemporary, and engineered feel. Weights have been specifically calibrated for light mode: headlines utilize Semi-Bold (600) and Bold (700) to stand out against the white background, while body copy remains at Regular (400) to ensure high legibility in long-form text.

- **Headlines:** Feature slightly tightened letter-spacing to create a "locked-in" professional appearance.
- **Labels:** Small labels use an increased weight and optional uppercase tracking to differentiate them clearly from body text.
- **Scalability:** On mobile devices, the `headline-xl` role downscales to 32px to ensure titles do not break awkwardly or overwhelm the viewport.

## Layout & Spacing
The layout logic follows a **Fixed-Fluid Hybrid Grid**. Content is housed within a 1280px max-width container on desktop, centered with fluid margins. 

- **Grid:** A 12-column grid system is used for desktop (24px gutters). For tablet (768px - 1024px), this transitions to an 8-column grid. Mobile (below 768px) uses a 4-column grid with 16px side margins.
- **Rhythm:** An 8px linear scale (with a 4px "half-step" for tight UI components) governs all padding and margin decisions. 
- **Verticality:** Sections are separated by large white space gaps (64px+) to reinforce the "Institutional" atmosphere, preventing the interface from feeling cluttered or "SaaS-generic."

## Elevation & Depth
Depth is achieved through **Ambient Shadows** rather than borders. This creates a soft, layered environment where the interface feels light and breathable.

- **Level 0 (Base):** #FFFFFF background. No shadow.
- **Level 1 (Cards/Containers):** Used for standard modules. Shadow: `0px 2px 8px rgba(0, 0, 0, 0.04)`.
- **Level 2 (Popovers/Dropdowns):** Used for interactive overlays. Shadow: `0px 8px 24px rgba(0, 0, 0, 0.08)`.
- **Level 3 (Modals):** Highest priority. Shadow: `0px 16px 48px rgba(0, 0, 0, 0.12)`.

Borders are strictly limited to internal dividers (1px, #F0F0F0) or input field boundaries, ensuring the overall aesthetic remains soft and expansive.

## Shapes
The shape language is **Refined and Intentional**. A standard radius of 0.5rem (8px) is applied to most containers and buttons. This provides a balance between the clinical sharpness of finance and the approachability of modern tech.

- **Standard (8px):** Primary buttons, input fields, and small cards.
- **Large (16px):** Main content modules and modal containers.
- **Extra Large (24px):** Large hero sections or featured promotional containers.

## Components
- **Buttons:** Primary buttons use a solid #0D47A1 background with white text. Secondary buttons use a #F8F9FA background with #0D47A1 text. No borders.
- **Input Fields:** Use a subtle 1px border (#E0E0E0) that transitions to #1A73E8 on focus. Background is #FFFFFF.
- **Cards:** Cards should have no border; instead, use the Level 1 Ambient Shadow. The background is always #FFFFFF.
- **Chips/Badges:** Small, 4px rounded shapes with #F8F9FA backgrounds and #4A4A4A text for neutral states, or light blue tints for active states.
- **Lists:** Clean rows separated by a 1px #F0F0F0 divider. High horizontal padding (24px) to maintain the airy feel.
- **Data Tables:** Clear, Semi-Bold headers in `label-sm` style. Alternate row striping is not used; instead, use subtle hover states on the entire row.