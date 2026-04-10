# Design System: The Ethereal Academic

**Concept**: "Digital Curator" — An organized and calm interface for educators.
Uses tone transitions and spacing instead of sharp dividers, based on a Light-mode Glassmorphism Sage palette.

---

## 1. Color & Surface

| Token | HEX | Usage |
|-------|-----|-------|
| `primary` | `#436834` | Primary actions, CTA, selected states |
| `primary-dim` | `#375c29` | Gradient end |
| `primary-container` | `#c3efad` | Success states, milestones |
| `secondary` | `#0060ad` | Secondary emphasis |
| `surface` | `#f8faf8` | Default background (Level 0) |
| `surface-container-low` | `#f1f4f2` | Large content area grouping (Level 1) |
| `surface-container` | `#eaefec` | Nested sidebars, auxiliary navigation (Level 2) |
| `surface-container-lowest` | `#ffffff` | Floating elements (Glass background) |
| `surface-dim` | `#d4dcd9` | Overlay backdrop |
| `on-surface` | `#2d3432` | Default text (Pure #000 is prohibited) |
| `on-surface-variant` | `#59615f` | Secondary labels |
| `outline-variant` | `#acb3b1` | Ghost Border (15% opacity) |
| `error` | `#a73b21` | Error states |

### No-Line Rule
- **Prohibit 1px solid borders** — Use background color transitions (`surface` hierarchy) for area separation.
- If a border is unavoidable: Use `outline-variant` with 15% opacity (**Ghost Border**).

### Glass & Gradient Rules
- **Floating Elements** (Modals, Dropdowns, Sticky Headers): `surface-container-lowest` 70% opacity + `backdrop-filter: blur(12px)`.
- **Hero / Primary CTA Gradients**: `primary` → `primary-dim`, 135° linear-gradient.

---

## 2. Typography

| Role | Font | Size | Notes |
|------|------|------|-------|
| Display / Headline | Manrope | `display-lg` 3.5rem | `letter-spacing: -0.02em`, Bold |
| Interface / Body | Inter | `body-md` 0.875rem | Default body |

- Secondary labels: Use `on-surface-variant` (#59615f) to reduce eye strain.

---

## 3. Elevation & Depth

- **Prioritize Layering**: Express depth through container hierarchy overlap instead of shadows.
  - e.g., `surface-container-lowest` card on `surface-container-low` → Natural floating effect.
- **Floating Shadows** (FAB, etc.): `box-shadow: 0 12px 32px rgba(45, 52, 50, 0.06)` — Use `on-surface` for shadow tint, pure black is prohibited.

---

## 4. Components & Layouts

### Sidebar Navigation
- **Collapsible Behavior**: Side navigation transitions between fully expanded and collapsed states (width adjusted, text hidden).
- **Primary Navigation Selection**: Active state uses a right border (`border-r-4 border-green-800`), green text, and a light green background (`bg-green-50/50`).
- **Submenu Navigation Selection**: Active state uses a subtle pill-shaped background (`bg-primary/10`) with primary colored text.
- **Icons**: Material Symbols Outlined.

### SPA View (Observation Journal Pipeline)
The pipeline operates as a unified SPA view (`ObservationPage`) handling transitions between template selection, creation, log generation, and result views via view state management.

- **Main Container**: `glass-panel rounded-[1.5rem] p-5 sm:p-8 shadow-sm border border-white/40`.
- **View Header**: Used consistently across sub-views for back navigation and view-specific actions.
- **Loading Overlay**: Full-page blurring overlay with a spinning icon (`RefreshCw`) for generation processes.

#### View Transition Animation
- **Header Placement**: `ViewHeader` must be placed **outside** the animated content area. This keeps the header fixed during transitions, with only the title changing based on view state.
- **Content Animation**: Only the content area uses `animate-view-enter`/`animate-view-exit` classes via `useViewTransition` hook.
- **List View**: When returning to a list view (e.g., from detail to list), skip the enter animation to avoid visual noise. Use conditional: `exitingView ? 'animate-view-exit' : viewState === 'list' ? '' : 'animate-view-enter'`.
- **List Items**: Do **not** apply stagger animations to list items. Items should appear all at once for cleaner UX, especially when navigating back and forth frequently.
- **Dynamic Form (Hierarchical JSON Visualization)**:
  - **Depth 0 (Root)**: `surface` background, `rounded-2xl`, with a subtle border.
  - **Depth 1 (Section)**: `surface-container-low/50` background, `rounded-xl`.
  - **Depth 2 (Sub-section)**: Left border (`border-l-4 border-primary/30`), left padding.
  - **Text Inputs**: Textareas mapped to terminal nodes. Each includes an inline OCR upload button.
- **Log Result View**:
  - **Version History**: Controlled via a dropdown `<select>` element.
  - **Result Cards**: Display hierarchical path breadcrumbs, content, and inline action buttons (Copy, Add Comment).
  - **Comments**: Expanding inline textarea section within the active result card.
  - **Footer Action Bar**: Contains the "Regenerate" button enabled when comments are present.
- **Image Editing (Cropping) UI**:
  - `ImageCropperModal`을 통해 이미지 업로드 전 편집 단계를 제공한다.
  - **Interaction**: 회전(90도 단위), 영역 선택(Drag to Resize), 자동 Aspect Ratio(옵션).
  - **Visuals**: 다크 배경의 집중형 모달, Glassmorphism 액션바, `Lucide` 아이콘 사용.

---

## 5. Mobile & Responsive Strategy

**Direction**: "Desktop-First, Mobile-Optimized"

### Core Guidelines
- **Fluid Layout**: Use relative sizing (`%`, `vw`) or Tailwind's responsive prefixes (`sm:`, `md:`).
- **Mobile Menu**: Sidebar converts to a sliding drawer with a backdrop overlay on small screens.
- **Space Efficiency**: Padding on main containers shrinks (e.g., `p-4 sm:p-6 md:p-10`) on smaller screens.

---

## 6. Do / Don't

| Do ✅ | Don't ❌ |
|--------|----------|
| Use ample spacing (`spacing-10/12`) | Use pure `#000000` text |
| Apply `rounded-xl` or `rounded-2xl` to main containers | Use 1px solid borders for separation |
| Use `primary-container` (#c3efad) for success/milestones | Use high-saturation Alert Red → Use `error` (#a73b21) token |

---

*Last Updated: 2026-04-07*