# Project Brief: Threadthulhu City Map

## The Vision in One Sentence
An explorable, game-like city that *is* Visa's mind — built from his actual tweet archive, navigable like Civilization, where the shape of the city reflects the shape of his thinking.

## The Subject
**Visakan Veerasamy (@visakanv)** — Singaporean writer, prolific Twitter thinker, known for an enormous interconnected web of threads spanning 15+ years. Venkatesh Rao coined the term **"threadthulhu"** to describe it: a Lovecraftian hyperobject, tangled, densely interlinked, promiscuously forking, fundamentally untameable. He said it would take AGI to properly render it.

We are not trying to tame it. We are building it a map.

## The Core Insight
**Maps are honest about incompleteness.** A map doesn't pretend to show everything — it shows terrain, landmarks, routes, and says "here be dragons" in unexplored places. This is the most truthful representation of Visa's archive. Most people have only ever visited a tiny corner of it. The map makes that visible and makes exploration possible.

## The Two Source Threads

### Thread 1: Graph Paper / Spatial Information (Nov 2020)
- Core thesis: graph paper / infinite 2D canvas is an underrated interface for information
- Linear formats (Twitter, web pages) waste cognitive potential
- The r/place example: 1000x1000 pixels of dense layered meaning you zoom into or out of
- Key balance: density must be **navigable**, not just dense
- Zoom level IS the interface

### Thread 2: Browser Tab as Video Game (Jan 2015)
- Dream: a "game" in a browser tab that feels like a video game dashboard
- Inspired by Civilization's "build your city" mechanic — start simple, unlock things over time
- Pokémon's satisfying progression, WoW's character that visibly reflects growth
- Ideas don't go from 0→done, they increase their power level over time
- Key feeling: **satisfying**, **auto-clicking**, sense of progression and discovery

## The Concept: Threadthulhu City

A city where:
- **Neighborhoods = major recurring themes** (friendship, Twitter-as-game, identity, writing, focus, Singapore, race, productivity, creativity, etc.)
- **Buildings = individual threads** — size reflects length/engagement
- **Streets = connections between themes** — width reflects how often themes link
- **Time is an axis** — older parts of the city feel established and dense; recent tweets are the frontier/construction zone
- **Zoom = the interface** — far out you see the whole city; zoom in and you're reading individual tweets

## Design Principles

1. **Fog of war** — threads you haven't read are dimly visible, not fully rendered
2. **Landmarks** for legendary threads (high engagement, frequently referenced)
3. **Hidden alleys** for obscure gems (3 likes, secretly brilliant)
4. **Game feel** — movement feels like exploring, not scrolling
5. **Honest incompleteness** — the map doesn't pretend to show everything
6. **The city builds itself** as Visa posts — it's a living document

## Visual Aesthetic
Civilization meets old illustrated city maps. Not a data dashboard. Not a social media UI. Something that feels like an artifact, a world.

## Data Source
- **Community Archive** (communityarchive.org) — Visa's full tweet archive is available here
- He is a close friend of the builder and can provide direct archive access if needed

## Technical Stack
- **Claude Code** for all development (vibecoding)
- **React** for the frontend
- **Semantic embeddings** to cluster tweets into neighborhoods
- **D3 or canvas library** for the city rendering
- **The clustering output determines the neighborhoods** — this is data-driven, not decided in advance

## Build Order
1. **Data pipeline** — fetch archive, embed tweets semantically, cluster into themes, understand what the neighborhoods actually are
2. **Simple canvas** — neighborhood blobs, no visuals yet, validate clustering makes sense
3. **City rendering** — make it beautiful, add zoom/pan
4. **Game feel** — movement, fog of war, landmarks, progression

## The Most Important Early Question
What do the neighborhoods actually turn out to be? The clustering might surprise us. Don't pre-decide the themes — let the data speak first.

## The Pitch (when showing Visa)
> "The threadthulhu doesn't need to be killed. It needs a map. And maps don't capture everything — they just make exploration possible."
