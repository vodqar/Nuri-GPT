# UI/UX Technical Guide

## View Transition Consistency

### Standardized Header Row (`.view-header-row`)
To prevent vertical shifting (jitter) when switching between view states within the same container, all sub-headers must use a standardized class that defines a consistent height.

- **Class**: `.view-header-row`
- **CSS Definition**:
  ```css
  .view-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 52px; /* Standardize based on tallest possible element (mode-toggle) */
  }
  ```
- **Usage**: Use `view-header-row` as the direct parent of header text/actions.

## Action Pill UI Standard

To maintain visual harmony, all header-level action controls (buttons and toggles) follow a standardized "Pill" design language.

- **Shared Shape**: `9999px` border-radius (full pill).
- **Core Height**: `40px` total height for the container or standalone button.

### 1. Standalone Pill Button (`.manage-btn`, `.copy-all-btn`)
Used for single-action toggles or commands.

- **Idle**: `var(--color-surface-container-low)` background, `600` font-weight.
- **Active**: `var(--color-primary)` background, `white` text, subtle elevation shadow.
- **Hover**: Subtle lift and background change to `var(--color-surface-container-high)`.

### 2. Segmented Control (`.mode-toggle`)
Used for switching between mutually exclusive modes (e.g., Auto/Manual).

- **Structure**: A container with a low-contrast background holding multiple smaller pill buttons.
- **Container padding**: `4px` all around.
- **Active Segment**: White background, `var(--color-primary)` text, `0 2px 8px` shadow.
- **Inactive Segment**: Transparent background, `var(--color-on-surface-variant)` text.

### Visual Spec Sheet
| Element | Border Radius | Height | Font Weight | Focus Transition |
| :--- | :--- | :--- | :--- | :--- |
| Header Row | N/A | 52px (min) | N/A | N/A |
| Action Pill | 9999px | 40px | 600 | 0.25s cubic-bezier |
| Segment | 9999px | 32px | 600 | 0.2s cubic-bezier |
