# Onboarding guide — Earthsandwich

Generated at: 2026-04-29  |  Developer: Ethan  |  Level: junior

---

## What this project is

Earthsandwich is a read-only travel travelogue web app that lets friends and family follow a round-the-world trip in real time. The site centers on an interactive Google Map that plots the trip route — visitors can see which stops have been visited (shown differently from planned ones) and drill into individual cities to read posts, view photos, or catch up on long-form travel writing.

The content (50+ stops, photos, Instagram captions, Substack articles) is all hard-coded at build time — no database, no server, no login. The site is a static single-page app built with React, TypeScript, and Vite, and is meant to be hosted on something like GitHub Pages or Netlify.

The two types of users are the travelers themselves (who will add content between trips) and their audience (friends and family who browse). Right now, only the read-only viewing experience is in scope.

---

## How the workflow works here

This project uses a process called **SDD — Spec-Driven Development**. It's a structured way to go from an idea to working code, using a set of slash commands (called `/speckit.*` commands) to guide each step. Here's how the cycle works:

1. **Specify** — `/speckit.specify` turns a natural-language feature description into a formal `spec.md`. This is the source of truth for what you're building and why.
2. **Plan** — `/speckit.plan` reads the spec and produces `plan.md`, which translates requirements into a technical design: stack choices, project structure, component breakdown.
3. **Tasks** — `/speckit.tasks` reads the plan and spec and writes `tasks.md` — a dependency-ordered checklist of concrete implementation tasks.
4. **Implement** — `/speckit.implement` works through `tasks.md` one task at a time, writing the actual code.

All three planning artifacts for this project already exist under `specs/001-world-travelogue/`. Your job as you join is to start working through the implementation tasks in `tasks.md`.

**After you finish implementing a feature**, run `/speckit.learn.review` — it produces an educational guide explaining the technical decisions that were made, which is a great way to consolidate what you learned from working through the code.

---

## Features in progress

### World Travelogue — in progress

An interactive travel travelogue with a Google Maps canvas, a trip feed sidebar, and a modal stop-detail overlay. Visitors can explore a round-the-world trip at the continent level, drill into individual regions, and open full-detail pop-ups for Instagram and Substack posts.

Open tasks: 50  |  Next: T001 · Initialize Vite React TypeScript project

---

## Where to start

These tasks are recommended for your level — low complexity, no blockers, and a good way to get oriented in the codebase:

1. **T009** · Setup global CSS styling framework — *World Travelogue*
   Why: Pure CSS work, no logic dependencies, and touching `src/styles/global.css` gives you a quick tour of the visual structure before you touch any components.

2. **T010** · Setup responsive grid layout for map and sidebar — *World Travelogue*
   Why: Builds directly on T009, still CSS-only, and teaches you the 72/28 map-plus-sidebar split that every view in the app is built around.

3. **T013** · Add visited vs. planned marker styling — *World Travelogue*
   Why: Short, focused CSS task in `src/styles/map.css`; gives you your first look at the map layer without having to understand all of `MapView.tsx` up front.

4. **T008** · Refactor hard-coded itinerary data to flat model — *World Travelogue*
   Why: Working in `src/data/itinerary.ts` is a great way to learn the data shape the whole app is built on, before any components come into play.

5. **T004** · Create entry point (`index.html` and `src/main.tsx`) — *World Travelogue*
   Why: The smallest possible code change — wiring the React root into the HTML shell — and lets you run the app locally for the first time.

---

## Project glossary

**Spec** (`spec.md`) — The formal description of a feature: what it must do, who it's for, and what success looks like. In this project: `specs/001-world-travelogue/spec.md`.

**Plan** (`plan.md`) — The technical design that translates the spec into architecture: what stack to use, how to structure the files, what components to build. In this project: `specs/001-world-travelogue/plan.md`.

**Task** — One concrete, checkable unit of implementation work. Tasks are listed in `tasks.md` and ordered by dependency. A task marked `[P]` can be done in parallel with other `[P]` tasks in the same phase.

**Feature** — A self-contained unit of functionality defined by a spec/plan/tasks triple. This project currently has one feature: `001-world-travelogue`.

**Hook** — An automated action that fires when something specific happens (e.g., after a task is completed). This project doesn't have custom hooks configured yet.

**Drift** — When the code diverges from the spec — for example, if a component does something the spec doesn't allow, or a requirement was missed. `/speckit.analyze` detects drift by cross-checking spec, plan, and tasks for consistency.

**SDD** — Spec-Driven Development. The workflow this project uses: specify → plan → tasks → implement.

**Region** — In this app, a dynamic grouping of nearby stops based on the closest international airport. Not a stored database record — computed at build time from stop coordinates.

**Stop** — One entry in the trip itinerary. Has a date, location, coordinates, visited/planned status, and a post type (Instagram or Substack).

**speckit** — The set of slash commands (`/speckit.*`) that drive the SDD workflow.

**learn** — An extension that adds educational slash commands. `/speckit.learn.review` is the main one to use after implementing a feature — it explains *why* the code was written the way it was.

**onboard** — The extension you're using right now. Provides `/onboard start`, `/onboard explain`, `/onboard trail`, `/onboard quiz`, and more. Helps new developers get oriented and build confidence before writing code.

---

## Active extensions and how they affect your day-to-day

| Extension | Commands | What it does during your work |
|-----------|----------|-------------------------------|
| **speckit** (core) | `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, `/speckit.clarify`, `/speckit.analyze`, `/speckit.checklist` | Drives the full feature lifecycle — from idea to implemented code. You'll use `/speckit.implement` most day-to-day to work through `tasks.md`. |
| **learn** | `/speckit.learn.clarify`, `/speckit.learn.diagrams`, `/speckit.learn.review` | Adds educational depth to the SDD commands. Use `/speckit.learn.review` after finishing a feature to read an explanation of the design decisions made. Use `/speckit.learn.diagrams` if you want visual architecture diagrams to understand how the pieces fit together. |
| **onboard** | `/speckit.onboard.start`, `/speckit.onboard.explain`, `/speckit.onboard.trail`, `/speckit.onboard.quiz`, `/speckit.onboard.badge`, `/speckit.onboard.mentor`, `/speckit.onboard.team` | Helps you get up to speed and stay oriented. `/speckit.onboard.explain <file>` is especially useful when you open an unfamiliar file and want a plain-English walkthrough before reading the code. `/speckit.onboard.trail <feature>` shows you the dependency chain so you know what order to tackle tasks. |
