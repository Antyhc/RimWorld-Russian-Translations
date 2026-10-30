# RimWorld — Russian Mod Translations

[Русский](README.md) · [Registry](registry.json) · [Status](PROJECT_STATUS.md) · [Contributing](CONTRIBUTING.md)

Russian localization maintenance for RimWorld mods: missing text, upstream
contributions and standalone packs with confirmed distribution rights.
A registry record alone is not an installable release.

Public releases for **RimWorld 1.7**, checked 30 October 2026:

| Mod | Package entries | Steam Workshop |
|---|---:|---|
| [Blood Animations](https://steamcommunity.com/sharedfiles/filedetails/?id=3830000511) | 3 | Public |
| [Loading Progress](https://steamcommunity.com/sharedfiles/filedetails/?id=3830035919) | 399 | Public |
| [Mechanoid Upgrades](https://steamcommunity.com/sharedfiles/filedetails/?id=3828883103) | 108 | Public |
| [Smart Medicine - Continued](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790822) | 7 | Public |
| [Designator Shapes](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790605) | 208 | Public |
| [Reel's Expanded Storage](https://steamcommunity.com/sharedfiles/filedetails/?id=3830014953) | 2 | Public |
| [Reel's Turret Pipeline](https://steamcommunity.com/sharedfiles/filedetails/?id=3830009448) | 21 | Public |
| [Yet Another Research Tree (YART)](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790757) | 30 | Public |
| [No Burn Metal](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790442) | 19 | Public; now included upstream, standalone pack unnecessary for new installs |
| [Vanilla Achievements Expanded](https://steamcommunity.com/sharedfiles/filedetails/?id=3830022947) | 1 | Public |
| [Vanilla Traits Expanded](https://steamcommunity.com/sharedfiles/filedetails/?id=3830032379) | 2 | Public |
| [WVC - Work Modes](https://steamcommunity.com/sharedfiles/filedetails/?id=3830010549) | 23 | Public |

Seven new releases on 30 October: Blood Animations, Turret Pipeline, WVC Work Modes,
REEL Storage, Achievements, Traits and Loading Progress. All 451 values passed actual isolated English
control/Russian candidate checks on **1.7.4990 rev 1069**. Subscribed byte-exact
Workshop copies were then actually loaded. The preserved real English control
was reused only after identical source/context/game/probe verification. Full
localization-error multisets were unchanged within each pair. Achievements was
checked with Odyssey enabled and disabled; it injects nothing without that DLC.
Loading Progress also passed a fresh control/candidate pair for its actual
early 399-entrycache; the Workshop run showed Russian transient progress text,
startup time, tooltip and report empty-state. No saves, colony playthrough or
extended gameplay were tested.

These are scoped supplements. Blood Animations adds two captions and a Russian
settings heading; its existing Russian pack is recommended for other text.
Turret Pipeline contains 21 core entries, excluding four optional Factory entries.
WVC requires Biotech and preserves existing Russian. Storage adds two fridge
fields; mandatory Adaptive Storage Framework still declares versions only through
1.6, so translation startup does not certify all dependency mechanics.
Achievements localizes one descriptive Odyssey title, preserving game names and
acronyms. Traits additionally requires OliveWizard's main Russian pack 2337425872
and adds two internal effect-stage captions; newly visible ordinary UI text is
not promised. Third-party Russian is not copied into these supplements. Loading Progress is
a complete 399-keyown provider because its loader does not merge partial packs.
Disable old ilyvion.loadingprogress.ru 3585898788 if installed; the new pack does
not disable other mods automatically.

No Burn Metal Russian was accepted into the original; all 19 entries are already
present in its current Workshop distribution. The old separate page remains with
guidance. ReGrowth was accepted into [community translation PR46](https://github.com/OneCodeUnit/VanillaRussianExpanded/pull/46)
and the accepted variant is in its Workshop copy. [Shapes15](https://github.com/merthsoft/designator-shapes/pull/15)
and [YART6](https://github.com/csh1668/YetAnotherResearchTree/pull/6) remain open,
conflict-free, with no human change requests. [Verified replies](community/author-responses-2026-10-30.json).
Nine missing VEF strings were offered to the existing community translation in
[PR47](https://github.com/OneCodeUnit/VanillaRussianExpanded/pull/47); this
contribution has static QA, with no new game-test claim.

[Collection3830036321](https://steamcommunity.com/sharedfiles/filedetails/?id=3830036321)
was created through the official web wizard with our cover, bilingual description
and 12 verified members. It remains private: the Publish button does not complete,
and native visibility-only submission returns 15 AccessDenied. Public availability
is not claimed; use direct item links above. Earlier failed native draft 3828791160
is retained and superseded.

## Installation

Subscribe to the original and the chosen language pack, enable both, load the
translation after the original, and select Russian. Follow each item's actual
mod/DLC requirements. Traits also requires the main Russian pack; recommendations
for other packs are not mandatory dependencies. Enable one copy per packageId.
For manual installation, copy only `mods/<packageId>/payload/` into a separate
`RimWorld/Mods/` folder. A record without `payload/` is not installable.

## Rights and maintenance

[Oskar Potocki permitted independent text translations for 23 named Vanilla Expanded mods](community/vanilla-expanded-text-permission-2026-10-30.json),
including disclosed AI assistance. No Vanilla Expanded endorsement or association
is claimed. Original artwork and third-party translations are outside this grant.
Our covers are original typographic designs with RUSSIAN lettering.
[AOBA permission request](https://github.com/AobaKuma/MechsuitFramework/issues/34)
remains unanswered; unconfirmed-rights material is held. Credits, changes and
licenses are recorded per pack; CC BY-NC-SA adaptations retain those terms.

The registry dynamically discovers `mods/*/manifest.json`:166records from156saved
translation stores and 10 additional batch/draft records, with no fixed size limit.
Monitoring covers 166 original Workshop IDs,24 GitHub repositories and 5 PRs.
Source changes enter review; monitoring is not an autonomous translator/publisher.
Official native collection membership updates are implemented and verified;
website publication is a separate check. [Maintenance](docs/MAINTENANCE.md).

Private 28 October results are historical:3474 values in 42 packs plus 473 new values,
3947/3947 actual readbacks. All 616 drafts were processed:291 retained,315 revised,
10 held. This does not make every text release-ready. Following NoBurn/ReGrowth
updates, the old combined-profile guard correctly refuses launch pending retest;
its hashes were not weakened. All 9 old version-compatibility warnings remain.
[Private-batch counts](reports/reviewed-batches-2026-10-28.json).

AI-assisted authoring and semantic review are disclosed; independent human
proofreading is not claimed. Technical checks, actual field readback and colony
playtesting are distinct. The user's main configuration was backed up and stayed
unchanged throughout isolated testing.
