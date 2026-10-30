# RimWorld — Russian Mod Translations

[Русский](README.md) · [Registry](registry.json) · [Project status](PROJECT_STATUS.md) · [Contributing](CONTRIBUTING.md)

Russian localization maintenance for RimWorld mods. We contribute translations
upstream and release standalone packs with confirmed rights after checking
current sources and existing Russian translations.

Releases for **RimWorld 1.7**, as checked on30October2026:

| Translation | Translated entries | Availability |
|---|---:|---|
| [No Burn Metal](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790442) | 19 | Included in original; separate pack no longer needed for new installs |
| [Designator Shapes](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790605) | 208 | Public page verified anonymously |
| [Yet Another Research Tree](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790757) | 30 | Public page verified anonymously |
| [Smart Medicine — Continued](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790822) | 7 | Public page verified anonymously |
| [Mechanoid Upgrades](https://steamcommunity.com/sharedfiles/filedetails/?id=3828883103) | 108 | Public page verified anonymously |
| [Blood Animations](https://steamcommunity.com/sharedfiles/filedetails/?id=3830000511) | 3 | Public: 2 absent captions plus a localized settings heading |
| [Reel’s Turret Pipeline](https://steamcommunity.com/sharedfiles/filedetails/?id=3830009448) | 21 | Public; core only, 4 optional Factory entries excluded |
| [WVC Work Modes](https://steamcommunity.com/sharedfiles/filedetails/?id=3830010549) | 23 | Public; requires Biotech |
| [Reel’s Expanded Storage](https://steamcommunity.com/sharedfiles/filedetails/?id=3830014953) | 2 | Steam creation confirmed; website access checked separately |

YART and Smart Medicine fill missing strings while preserving their 79 and 48
bundled Russian entries. All four subscribed Workshop copies were loaded in an
isolated **RimWorld 1.7.4990** profile: all 264 expected values matched, and four
settings windows were inspected. Nine Core localization errors were identical
to the baseline; the packs added no localization errors. Personal configuration
hashes were unchanged. No colony playthrough or extended gameplay test was done.

Mechanoid Upgrades passed two separate minimal loads with Core, Biotech,
Harmony and the original: 108/108 English control and Russian values matched;
the existing 52 localization errors were unchanged. This tests the prepared
package; all 18 subscribed Workshop files matched the package exactly, while
an actual load from that Workshop copy also verified all 108 Russian values
with no additional localization errors. Biotech was
also added and verified as required DLC metadata on Workshop.

The [collection](https://steamcommunity.com/sharedfiles/filedetails/?id=3828791160)
has been created through Steam API with nine members, but website publication
is blocked by Steam error 15, “Access denied”, when the owner saves its title
and description. Use the direct item links above.

As of 28 October 2026, **166 mods** are tracked: 156 saved-store records plus ten
additional metadata records for existing reviewed batches and drafts. The old
156 records had 156 unique source IDs; omitted draft stores caused the scope
gap. A registry record does not imply a release, distribution rights or a game
test. Unreviewed machine drafts are excluded from release payloads.

Open upstream contributions: [Designator Shapes](https://github.com/merthsoft/designator-shapes/pull/15),
[No Burn Metal](https://github.com/Nonunon/NoBurnMetal/pull/1), and
[YART](https://github.com/csh1668/YetAnotherResearchTree/pull/6). A ReGrowth addition was
submitted to [Vanilla Russian Expanded #46](https://github.com/OneCodeUnit/VanillaRussianExpanded/pull/46),
a community translation repository; original-native acceptance is not claimed.
No Burn Metal was merged into the original and is already distributed through Steam; new installations no longer need its separate pack. ReGrowth was merged into the community translation and is present in that Workshop copy. Shapes and YART remain open without requested changes. [Verified responses](community/author-responses-2026-10-30.json).

Separately from public releases, 42 managed private packs passed a 3474-value
load check. Codex individually reviewed all 616 local-model drafts: 291 unchanged,
315 revised and ten held. A strict private candidate contains 473 values from
eight mods; the actual combined readback matched **3947/3947** values. The complete
988-error language baseline was unchanged, with zero added errors. The stage
preserved 136 existing Russian values, coalesced 20 equivalent targets, held
87 targets and retained three brand names. This is isolated load/field testing,
not a colony playthrough, approval to install all 606 linguistic candidates or
permission to publish protected text. [Counts and evidence hashes](reports/reviewed-batches-2026-10-28.json)
are public; these private translation texts are not. Four Rimatomics settings
captions remain English; Runtime98 does not cover the entire UI. After the Dubs
Mint Menus update, two fresh game boots again matched 3947/3947 values and the
isolated-profile launcher guard now passes. It applied 96 UI handlers and held
two handlers from the changed DLL, preserving the assembly hash guard.

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
The previews are original typographic designs with a consistent `RUSSIAN`
caption. They use no original mod artwork; permission requests for original
previews remain separate. Other translations with unconfirmed distribution
rights are held from publication.
A [single permission request](https://github.com/AobaKuma/MechsuitFramework/issues/34)
covers five AOBA mods; no response or distribution permission is claimed.

Translations are AI-assisted. `ai_reviewed` means an AI semantic review against
the source; independent human proofreading is not claimed. Static checks,
game loading and gameplay tests are distinct evidence. Community translations
retain their own credits and licenses. For example,
[Vanilla Russian Expanded](https://github.com/OneCodeUnit/VanillaRussianExpanded)
uses CC BY-NC-SA 4.0; its packages are not duplicated automatically.

## Maintenance

Every `mods/*/manifest.json` is discovered automatically, with no fixed mod
limit. Monitoring covers 166 original Workshop IDs, 24 official GitHub
repositories and four PRs. Workshop metadata detects mod updates; string
changes are checked where file sources are configured. Updates generate a
review queue while preserving existing Russian text. Translation and release
updates still require review. Collection membership changes were verified
through SteamUGC AddDependency; initial website publication is separate.

See [maintenance](docs/MAINTENANCE.md), [publishing](docs/PUBLISHING.md), and
[QA limits](docs/QA.md). Report translation problems through
[Issues](https://github.com/Antyhc/RimWorld-Russian-Translations/issues) with the
mod name, game version, key/screenshot and expected wording.

30October: four new packages passed their own English-control/Russian game loads,49values with no additional localization errors. Three were subscribed/downloaded through Steam with21exact files; installation and actual Workshop-copy game loading are separate checks. [Vanilla Expanded request #195](https://github.com/Vanilla-Expanded/VanillaExpandedFramework/issues/195) is pending and grants no rights. Backstories, Smart Speed and World Domination are held as equivalent existing Russian packs cover all prepared entries.
