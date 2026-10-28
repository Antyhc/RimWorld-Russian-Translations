# RimWorld — Russian Mod Translations

[Русский](README.md) · [Registry](registry.json) · [Project status](PROJECT_STATUS.md) · [Contributing](CONTRIBUTING.md)

Russian localization maintenance for RimWorld mods. We contribute translations
upstream and release standalone packs with confirmed rights after checking
current sources and existing Russian translations.

First releases for **RimWorld 1.7**:

| Translation | Translated entries | Availability |
|---|---:|---|
| [No Burn Metal](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790442) | 19 | Public page verified anonymously |
| [Designator Shapes](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790605) | 208 | Public page verified anonymously |
| [Yet Another Research Tree](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790757) | 30 | Public page verified anonymously |
| [Smart Medicine — Continued](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790822) | 7 | Submitted; Steam automatic content inspection pending |

YART and Smart Medicine fill missing strings while preserving their 79 and 48
bundled Russian entries. All four subscribed Workshop copies were loaded in an
isolated **RimWorld 1.7.4990** profile: all 264 expected values matched, and four
settings windows were inspected. Nine Core localization errors were identical
to the baseline; the packs added no localization errors. Personal configuration
hashes were unchanged. No colony playthrough or extended gameplay test was done.

The [collection](https://steamcommunity.com/sharedfiles/filedetails/?id=3828791160)
has been created through Steam API with four members, but website publication
is blocked by Steam error 15, “Access denied”, when the owner saves its title
and description. Use the direct item links above.

As of 28 October 2026, **166 mods** are tracked: 156 saved-store records plus ten
additional metadata records for existing reviewed batches and drafts. The old
156 records had 156 unique source IDs; omitted draft stores caused the scope
gap. A registry record does not imply a release, distribution rights or a game
test. Unreviewed machine drafts are excluded from release payloads.

Open upstream contributions: [Designator Shapes](https://github.com/merthsoft/designator-shapes/pull/15),
[No Burn Metal](https://github.com/Nonunon/NoBurnMetal/pull/1), and
[YART](https://github.com/csh1668/YetAnotherResearchTree/pull/6).
Author responses are pending; none has been accepted yet.

## Installation

Install the original mod linked in `original.workshop_url`, then subscribe to
the translation. Enable both, load the original before the translation, and
select Russian. These releases claim 1.7 support; earlier versions were not
tested. Enable one translation package per original when migrating from a
local copy.

For manual installation, copy the **contents of `payload/`** from the relevant
`mods/<packageId>/` folder into a separate folder under `RimWorld/Mods/`.
A registry folder without `payload/` is not an installable mod.

## Credits and validation

Original authors, links and license evidence are tracked per mod and in each
package. Original assemblies, textures and game assets are not redistributed.
The four previews are original typographic designs with a consistent `RUSSIAN`
caption. They use no original mod artwork; permission requests for original
previews remain separate. Other translations with unconfirmed distribution
rights are held from publication.

Translations are AI-assisted. `ai_reviewed` means an AI semantic review against
the source; independent human proofreading is not claimed. Static checks,
game loading and gameplay tests are distinct evidence. Community translations
retain their own credits and licenses. For example,
[Vanilla Russian Expanded](https://github.com/OneCodeUnit/VanillaRussianExpanded)
uses CC BY-NC-SA 4.0; its packages are not duplicated automatically.

## Maintenance

Every `mods/*/manifest.json` is discovered automatically, with no fixed mod
limit. Monitoring covers 166 original Workshop IDs, 24 official GitHub
repositories and three PRs. Workshop metadata detects mod updates; string
changes are checked where file sources are configured. Updates generate a
review queue while preserving existing Russian text. Translation and release
updates still require review. Collection membership changes were verified
through SteamUGC AddDependency; initial website publication is separate.

See [maintenance](docs/MAINTENANCE.md), [publishing](docs/PUBLISHING.md), and
[QA limits](docs/QA.md). Report translation problems through
[Issues](https://github.com/Antyhc/RimWorld-Russian-Translations/issues) with the
mod name, game version, key/screenshot and expected wording.
