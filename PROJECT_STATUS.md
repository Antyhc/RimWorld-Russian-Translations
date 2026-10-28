# PROJECT_STATUS

Generated from `mods/*/manifest.json` by `python scripts/rwtranslations.py registry`.

Last inventory generation (UTC): 2026-10-28T14:15:35+00:00

The registry tracks **166 mods**: 156 saved-store records and 10 additional draft/review metadata records; 0 records have unverified store scope. Saved stores can also contain unfinished drafts. Original and translation package IDs are separate namespaces. Discovery has no fixed mod limit.

Steam has confirmed 5 item submissions: **4 pages verified anonymously**, 1 awaiting automatic content inspection. A submitted item ID or public API visibility flag alone does not prove public page access.

| Workshop translation | Website state | Game QA evidence |
|---|---|---|
| [Mechanoid Upgrades](https://steamcommunity.com/sharedfiles/filedetails/?id=3828883103) | public; anonymous page verified | [passed](mods/gogatio.mechanoidupgrades/game-test-evidence.json) |
| [Smart Medicine - Continued](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790822) | submitted_public_automatic_content_check | [passed](mods/memegoddess.smartmedicine/game-test-evidence.json) |
| [Designator Shapes](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790605) | public; anonymous page verified | [passed](mods/merthsoft.designatorshapes/game-test-evidence.json) |
| [Yet Another Research Tree (YART)](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790757) | public; anonymous page verified | [passed](mods/seohyeon.yart/game-test-evidence.json) |
| [No Burn Metal](https://steamcommunity.com/sharedfiles/filedetails/?id=3828790442) | public; anonymous page verified | [passed](mods/unon.noburnmetal/game-test-evidence.json) |

Game QA: 372 expected Russian values loaded across the recorded isolated RimWorld 1.7.4990 rev1069 checks. Each linked evidence file records its own baseline errors, Workshop-copy verification and UI inspection scope. Personal configuration hashes were unchanged. This is load/readback testing, **not a colony playthrough or extended gameplay test**. No independent human proofreading is claimed.

Private reviewed batches: **42 managed packages / 3474 values tested**; 616 local-model tasks processed. The private model candidate has **473 values verified across 8 providers**; 3947 combined values matched. This is isolated load/readback testing, with no colony playthrough or main-profile installation approval. Translation rights and public release QA are separate. [Counts and evidence hashes](reports/reviewed-batches-2026-10-28.json).

Two fresh game boots verified the current upstream files and the same private candidate tree; the guarded isolated launcher now passes. Runtime UI handlers: **96 applied / 2 held** after the Dubs Mint Menus update; the assembly guard was preserved. Full UI translation is not claimed.

[Workshop collection](https://steamcommunity.com/sharedfiles/filedetails/?id=3828791160): **native item and membership created; website publication pending**. Membership uses native SteamUGC AddDependency with postcondition verification; website publication is a separate step.

Authenticated owner edit form returns Steam error15: Access denied when saving collection title/description, including after selecting the owned Preview.png. Five native members verified; website Publish remains incomplete.

Integration proposals:

- [Designator Shapes](https://github.com/merthsoft/designator-shapes/pull/15): pr_submitted.
- [ReGrowth 2](https://github.com/OneCodeUnit/VanillaRussianExpanded/pull/46): pr_submitted (community translation repository; original-native acceptance not claimed).
- [Yet Another Research Tree (YART)](https://github.com/csh1668/YetAnotherResearchTree/pull/6): pr_submitted.
- [No Burn Metal](https://github.com/Nonunon/NoBurnMetal/pull/1): pr_submitted.

Current pilot covers are original typographic fallback designs. Original-art permission requests remain separate and do not block these covers. Other records with unconfirmed translation rights are held from distribution.

The 13 source-drift packages were refreshed. Targeted repairs added 20 strings, updated seven Russian texts and preserved 15 correct translations with new source hashes across five packages. These repairs have no new in-game test. Large outstanding deltas and stale custom-field proofs remain under review; historical static findings are not a count of broken translations.

| Metric | Count |
|---|---:|
| translations | 166 |
| saved_store_records | 156 |
| draft_only_records | 10 |
| model_reviewed_tasks | 616 |
| model_held_tasks | 10 |
| private_model_test_values | 473 |
| store_scope_unverified | 0 |
| technically_checked | 5 |
| game_tested | 5 |
| github_metadata_records | 166 |
| github_published | 4 |
| workshop_submitted | 5 |
| workshop_published | 4 |
| pull_requests | 4 |
| accepted | 0 |
| awaiting_rights | 161 |
| needs_update | 13 |
| freshness_unverified | 161 |
| static_inventory_pass | 129 |
| static_inventory_flagged | 20 |
| static_findings | 49 |
| repository_monitors | 24 |
| pull_request_monitors | 4 |
| icon_permission_requests | 2 |
| workshop_public_pages_verified | 4 |
| workshop_content_check_pending | 1 |
| workshop_source_monitors | 166 |

Full per-mod states are in [registry.json](registry.json). Static QA and in-game testing are separate. Freshness unverified does not mean a confirmed upstream change. A manifest records work; pending rights or QA prevents staging a release. Monitoring checks configured source metadata/files and PRs; it does not autonomously translate or publish updates.
