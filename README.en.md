# RimWorld — Russian Mod Translations

[Русский](README.md) · [Registry](registry.json) · [Project status](PROJECT_STATUS.md) · [Contributing](CONTRIBUTING.md)

Russian localization maintenance for RimWorld mods. Upstream integration is the
first choice. Separate Workshop translations require confirmed distribution
rights, current-source QA and a check for existing equivalent Russian translations.

The initial inventory covers **156 localization projects** as of 28 October 2026.
A registry entry is a tracking record. It does not imply a downloadable translation,
permission to redistribute it, or a successful game test. Check the individual
`qa`, `rights`, `integration` and `publication` fields. Unreviewed machine drafts
are excluded from release payloads.

Initial upstream contributions: [Designator Shapes, 208 entries](https://github.com/merthsoft/designator-shapes/pull/15)
and [No Burn Metal, 19 settings entries](https://github.com/Nonunon/NoBurnMetal/pull/1).
Their Russian source files are available in the corresponding `mods/` folders.
Separate Workshop releases are held for existing-translation and preview-art
rights checks. Daily file monitoring is configured for 24 verified official
repositories; unconfigured records are explicitly reported as such.

## Installation

Install the original mod linked in `original.workshop_url`. Subscribe to the
translation only if its manifest has a verified `publication.workshop_url`.
For manual installation, copy the **contents of `payload/`** into a separate
folder under `RimWorld/Mods/`. Enable both mods, load the original before the
translation, and select Russian. Only versions in `supported_versions` are claimed.
Enable one translation package per original when migrating from a local copy.
A registry folder without `payload/` is not an installable mod.

## Credits and validation

Original authors, Workshop links and license evidence are tracked per mod.
Original assemblies, textures and other game resources are not redistributed.
Community translations retain their own licenses and credits. A known source,
[Vanilla Russian Expanded](https://github.com/OneCodeUnit/VanillaRussianExpanded),
uses CC BY-NC-SA 4.0. Existing maintained translations should not be duplicated.
Local use of its strings does not imply that they have been republished here.

Translations are AI-assisted. `ai_reviewed` means an AI semantic review against
the source, not independent human proofreading. Static checks, actual game
loading and gameplay/UI tests are distinct evidence. Original Workshop artwork
with a `RUSSIAN` overlay needs separate image reuse/modification rights; a software
license is not treated as blanket permission for third-party artwork.

## Maintenance

Every `mods/*/manifest.json` is discovered automatically; there is no fixed mod
limit. Updates generate a review queue without replacing existing Russian text.
See [maintenance](docs/MAINTENANCE.md), [publishing](docs/PUBLISHING.md),
[QA limits](docs/QA.md), and [changelog](CHANGELOG.md).

Report translation problems through [Issues](https://github.com/Antyhc/RimWorld-Russian-Translations/issues)
with the mod name, game version, key/screenshot and expected wording.
Verified Workshop releases and the collection will be linked after they exist.
