# RimWorld — Russian Mod Translations

[Русский](README.md) · [Registry](registry.json) · [Status](PROJECT_STATUS.md) · [Contributing](CONTRIBUTING.md)

Russian localization maintenance for RimWorld mods: missing text, upstream
contributions and standalone packs with confirmed distribution rights.
A registry record alone is not an installable release.

14 public releases for **RimWorld 1.7**, checked 30 October 2026:

| Mod | Package entries | Steam Workshop |
|---|---:|---|
| [Blood Animations](https://steamcommunity.com/sharedfiles/filedetails/?id=3830000511) | 3 | Public |
| [Loading Progress](https://steamcommunity.com/sharedfiles/filedetails/?id=3830035919) | 399 | Public |
| [Mechanoid Upgrades](https://steamcommunity.com/sharedfiles/filedetails/?id=3828883103) | 108 | Public |
| [Vanilla Factions Expanded - Empire](https://steamcommunity.com/sharedfiles/filedetails/?id=3830050048) | 12 | Public |
| [Smart Medicine - Continued](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790822) | 7 | Public |
| [Designator Shapes](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790605) | 208 | Public |
| [Reel's Expanded Storage](https://steamcommunity.com/sharedfiles/filedetails/?id=3830014953) | 2 | Public |
| [Reel's Turret Pipeline](https://steamcommunity.com/sharedfiles/filedetails/?id=3830009448) | 21 | Public |
| [Yet Another Research Tree (YART)](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790757) | 30 | Public |
| [No Burn Metal](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790442) | 19 | Public; now included upstream, standalone pack unnecessary for new installs |
| [Vanilla Achievements Expanded](https://steamcommunity.com/sharedfiles/filedetails/?id=3830022947) | 1 | Public |
| [Vanilla Traits Expanded](https://steamcommunity.com/sharedfiles/filedetails/?id=3830032379) | 2 | Public |
| [WVC - Work Modes](https://steamcommunity.com/sharedfiles/filedetails/?id=3830010549) | 23 | Public |
| [Vanilla Cooking Expanded](https://steamcommunity.com/sharedfiles/filedetails/?id=3830078437) | 24 | Public |

Nine new releases on 30 October: Blood Animations, Turret Pipeline, WVC Work Modes,
REEL Storage, Achievements, Traits, Loading Progress, Empire and Cooking. All 487 unique values passed actual isolated English
control/Russian candidate checks on **1.7.4990 rev 1069**. Subscribed byte-exact
Workshop copies were then actually loaded. The preserved real English control
was reused only after identical source/context/game/probe verification. Full
localization-error multisets were unchanged within each pair. Updated Achievements
passed new checks with Odyssey enabled and disabled, including its actual Workshop
copy: the title is not injected without DLC, and complete Player.log ERROR/FATAL
record multisets remain unchanged. An empty language container fixed the
"mod did not load any content" error without adding a dummy translation key.
Loading Progress also passed a fresh control/candidate pair for its actual
early translation cache containing 399 entries; the Workshop run showed Russian transient progress text,
startup time, tooltip and report empty-state. No saves, colony playthrough or
extended gameplay were tested.

Cooking passed four fresh local control/candidate pairs:
neither integration, Alpha Animals alone, Genetics alone and both together.
They loaded 0/6/18/24 translations respectively; inactive targets were not injected.
All 24 unique strings, localization-error multisets and complete ERROR/FATAL
records were verified with no new errors. Its byte-exact Workshop copy then
passed four fresh boots in those same contexts. The preserved actual English
controls were reused after verifying identical inputs.
[Local evidence](mods/vanillaexpanded.vcooke/game-test-evidence.json) ·
[Workshop evidence](mods/vanillaexpanded.vcooke/workshop-game-test-evidence.json).

These are scoped supplements. Blood Animations adds two captions and a Russian
settings heading; its existing Russian pack is recommended for other text.
Turret Pipeline contains 21 core entries, excluding four optional Factory entries.
WVC requires Biotech and preserves existing Russian. Storage adds two fridge
fields; mandatory Adaptive Storage Framework still declares versions only through
1.6, so translation startup does not certify all dependency mechanics.
Achievements localizes one descriptive Odyssey title, preserving game names and
acronyms. Traits additionally requires OliveWizard's main Russian pack 2337425872
and adds two internal effect-stage captions; newly visible ordinary UI text is
not promised. Third-party Russian is not copied into these supplements.
Empire adds 12 strings and requires Royalty and the main Russian pack
[2942002763](https://steamcommunity.com/sharedfiles/filedetails/?id=2942002763).
Cooking adds 24 captions and descriptions across 12 cheese-making processes and
requires the main Russian pack [2914375951](https://steamcommunity.com/sharedfiles/filedetails/?id=2914375951).
Alpha Animals and Vanilla Genetics Expanded are optional for Cooking: each
translation branch loads only when its corresponding mod is enabled.
Both main Empire and Cooking Russian packs declare versions only through 1.6;
their metadata was preserved. These 1.7 supplement tests verify the selected
strings with the base translation loaded, not the entire base translation or
all gameplay mechanics.
Loading Progress is
a complete provider with 399 independently authored values because its loader does not merge partial packs.
Disable old ilyvion.loadingprogress.ru 3585898788 if installed; the new pack does
not disable other mods automatically.

No Burn Metal Russian was accepted into the original; all 19 entries are already
present in its current Workshop distribution. The old separate page remains with
guidance. ReGrowth was accepted into [community translation PR46](https://github.com/OneCodeUnit/VanillaRussianExpanded/pull/46)
and the accepted variant is in its Workshop copy. [Shapes15](https://github.com/merthsoft/designator-shapes/pull/15)
and [YART6](https://github.com/csh1668/YetAnotherResearchTree/pull/6) remain open,
conflict-free, with no human change requests. [Verified replies](community/author-responses-2026-10-30.json).
Sixteen strings for VEF, Gravship Chapter 1, Events and Landmarks were offered to existing community translations in
[PR47](https://github.com/OneCodeUnit/VanillaRussianExpanded/pull/47); this
contribution has static QA, with no new game-test claim.
[Adaptive Storage Framework PR41](https://github.com/bbradson/Adaptive-Storage-Framework/pull/41)
offers 41 Russian values and retains the `Vanilla` name: 42 IDs in two XML files.
The PR is open, with static semantic/token QA only; no new game test or 1.7
compatibility certification is claimed.

[Collection 3830036321](https://steamcommunity.com/sharedfiles/filedetails/?id=3830036321)
was created through the official web wizard with our cover, bilingual description
and 14 members verified through the official Steam API. It remains private: the Publish button does not complete,
and native visibility-only submission returns 15 AccessDenied. Public availability
is not claimed; use direct item links above. Earlier failed native draft 3828791160
is retained and superseded.

## Installation

Subscribe to the original and the chosen language pack, enable both, load the
translation after the original, and select Russian. Follow each item's actual
mod/DLC requirements. Traits, Empire and Cooking also require their specified main
Russian packs; Empire requires Royalty and WVC requires Biotech. Alpha Animals
and Genetics remain optional for Cooking. Enable one copy per packageId.
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

The registry dynamically discovers `mods/*/manifest.json`: 166 records from 156 saved
translation stores and 10 additional batch/draft records, with no fixed size limit.
Monitoring covers 166 original Workshop IDs, 24 GitHub repositories and recorded PRs.
Source changes enter review; monitoring is not an autonomous translator/publisher.
Collection membership updates through the official Steam API are implemented and verified;
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
