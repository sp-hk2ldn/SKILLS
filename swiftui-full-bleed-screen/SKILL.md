---
name: swiftui-full-bleed-screen
description: Make SwiftUI iOS screens visually full bleed across the top and bottom safe areas while keeping tappable controls safely spaced. Use when a user says a screen, onboarding step, paywall, hero screen, modal, or CTA footer has white bands, safe-area strips, non-full-bleed edges, awkward bottom whitespace, controls too close to the home indicator, or navigation chrome breaking an edge-to-edge design.
---

# SwiftUI Full-Bleed Screen

Use this skill to fix edge-to-edge SwiftUI screens without sacrificing safe tap spacing. The goal is: background and material paint to the physical device edges; text and controls remain comfortably inside safe areas unless intentionally edge-aligned.

## Core Rule

Separate **painting** from **layout**:

- Paint backgrounds, hero images, footer scrims, and decorative materials with `.ignoresSafeArea()`.
- Keep interactive controls inside a safe-area-aware container with explicit padding.
- Do not solve full bleed by simply pushing buttons under the home indicator.

## One Safe-Area Source Of Truth

The safest default is to keep the root layout safe-area-aware and extend only paint beneath system chrome. Do **not** apply `.ignoresSafeArea()` to a `GeometryReader` and then use that same reader's `safeAreaInsets` to reconstruct safe layout. On a physical device that value can be zero because the reader's coordinate space has already been expanded.

Prefer native safe-area layout for controls:

```swift
var body: some View {
  ZStack {
    screenBackground
      .ignoresSafeArea()

    currentScreen
      .padding(.top, 20)
      .padding(.bottom, 14)
      .frame(maxWidth: .infinity, maxHeight: .infinity)
  }
}
```

Here the background paints edge to edge while SwiftUI places `currentScreen` inside the real top and bottom safe areas. Use `safeAreaInset` for sticky controls that must reserve space.

If an immutable ancestor already ignores the safe area, restructure that ancestor if possible. When restructuring is impossible, read `view.window?.safeAreaInsets` from a `UIViewRepresentable` after it attaches to the window and use that single value for every interactive child. Do not use a guessed device constant or treat a zero `GeometryProxy.safeAreaInsets` as a physical inset.

Keep one layout policy for:

- top navigation, close, and back controls;
- sticky bottom CTAs and their footer scrims;
- scroll-content clearance behind overlays;
- every state swapped inside the same full-screen transition host.

Never combine independently discovered insets across sibling screens and assume they refer to the same physical edge.

## Workflow

1. **Inspect the actual screenshot**
   - Check the top status area and bottom home-indicator area separately.
   - Decide whether the visible band is a true system/background band or just an intentional pale part of the artwork.
   - Save a simulator screenshot before and after the change.

2. **Remove unnecessary chrome**
   - Hide or remove navigation bars/titles on immersive onboarding, paywall, and hero screens.
   - Prefer an in-content brand eyebrow over a navigation title when the screen is meant to feel editorial/full bleed.
   - If the screen does not need navigation routing, do not wrap it in `NavigationStack`; it can paint safe-area caps white.

3. **Put the root background outside chrome**
   Prefer this structure for a self-contained onboarding/paywall flow:

   ```swift
   var body: some View {
     ZStack {
       screenBackground
         .ignoresSafeArea()

       ZStack {
         currentScreen
           .id(currentScreenID)
           .transition(screenTransition)
       }
       .frame(maxWidth: .infinity, maxHeight: .infinity)
       .background(Color.clear)
     }
   }
   ```

   If a `NavigationStack` is required, put the full-bleed background outside it and hide toolbar backgrounds:

   ```swift
   ZStack {
     screenBackground.ignoresSafeArea()
     NavigationStack { content }
       .background(Color.clear)
       .toolbarBackground(.hidden, for: .navigationBar)
   }
   ```

4. **Choose the footer pattern**

   Use `safeAreaInset` when the footer must reserve layout space, such as stacked controls or lists above a CTA:

   ```swift
   .safeAreaInset(edge: .bottom, spacing: 0) {
     VStack(spacing: 12) {
       primaryButton
       quietBackLink
     }
     .padding(.horizontal, 28)
     .padding(.top, 14)
     .padding(.bottom, 10)
     .background {
       footerGradient
         .ignoresSafeArea(edges: .bottom)
     }
   }
   ```

   Use a bottom overlay for a single CTA when the screen needs a stronger full-bleed feel:

   ```swift
   .overlay(alignment: .bottom) {
     primaryButton
       .padding(.horizontal, 28)
       .padding(.bottom, 14)
       .frame(maxWidth: .infinity)
       .background(alignment: .bottom) {
         footerGradient
           .frame(height: 132)
           .ignoresSafeArea(edges: .bottom)
       }
   }
   ```

   The overlay itself stays inside the safe area, so the button sits 14 pt above the home
   indicator on every device. Only the gradient extends to the physical edge.

   In a multi-state flow, prefer a root `safeAreaInset` or an overlay attached to a root that still respects the safe area. Avoid attaching the only CTA protection to an inner `ScrollView`; it can be clipped or shifted outside the visible transition host.

5. **Keep bottom whitespace intentional**
   - Full bleed does not mean the CTA should touch the physical bottom edge.
   - Leave a designed gap under the CTA, typically 12-20 pt depending on device/home-indicator geometry.
   - The gap must be painted by the screen background or footer material, not by the system default white.

6. **Avoid common failure modes**
   - `NavigationStack` can leave white safe-area caps even when child backgrounds ignore safe areas.
   - A `safeAreaInset` reserves space correctly but may still look like a band if its material is too opaque.
   - An overlay can look full bleed but cover scroll content unless the scroll content has enough bottom padding.
   - `.clipped()` on the transition host can cut a footer that intentionally ignores the bottom safe area.
   - A root `.ignoresSafeArea()` also expands navigation controls; apply it to paint layers, not the whole screen.
   - `GeometryProxy.safeAreaInsets` is not authoritative after that geometry reader has ignored the safe area.
   - A button anchored too low can be clipped or feel unsafe; validate on the simulator, not by code inspection.

7. **Verify**
   - Build and launch fresh on the target simulator.
   - Capture screenshots of every affected screen state.
   - Inspect the very top and bottom 30-60 px of the screenshot.
   - Confirm CTA spacing, home-indicator spacing, and scroll content clearance.
   - Run the focused UI test or smoke path for onboarding/paywall navigation.
   - Run `git diff --check`.
   - For any bug first observed on a physical device, a simulator screenshot is not sufficient closure. Install the fresh build and verify the top control and bottom CTA on that same device class before reporting the safe-area defect fixed.

## Visual Heuristics

- Top: status bar should sit over the same hero/gradient/material as the screen, not a flat white cap.
- Bottom: the area below the CTA should be a deliberate continuation of the footer/background, not a separate strip.
- CTA: visually primary, with breathing room below it; do not let it collide with or disappear under the home indicator.
- Back/secondary actions: prefer quiet text links below CTAs on immersive onboarding screens.
