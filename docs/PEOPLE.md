# People system: final architecture

**Base:** Plan 1 (prerender real clay geometry, garments as recipes). **Grafted in:** Plan 2's prototype gate, its Layers-node scaling and its height-by-scale; Plan 3's clip_children decals. **Fixes:** masks stored lossless; clips stored as world angles; dark tints clamped; athletic modelled as real geometry; no mirrored limbs.

## 1. Pieces and pivots (15 per body, front-ortho, one shared canvas per body)
| Piece | Pivot | End (child joint) |
|---|---|---|
| pelvis (root) | hip centre | waist |
| chest | waist | neck top |
| head | neck top | — |
| upper_arm L/R | shoulder | elbow |
| forearm L/R | elbow | wrist |
| hand L/R | wrist | — |
| thigh L/R | hip socket | knee |
| shin L/R | knee | ankle |
| foot L/R | ankle | — |

- Every joint has a round overlap bead on both pieces (the current `--cutout` arm method), so rotating never opens a gap.
- Pivots and ends go into glTF extras, then into the manifest in px.
- Left and right are rendered separately: Workbench STUDIO light is not symmetric, so mirroring would show light coming from opposite sides.

## 2. Body variants
- **Logical bodies: 37.** Baby, plus {child, teen, adult} × {f, m} × {tall, short} × {fat, skinny, athletic}.
- **Rendered shapes: 19.** Baby, plus 3 ages × 2 sexes × 3 builds. Height is not rendered.
- **Shape transform:** a BODY table of named bead chains (centre, radius) runs through:
  1. age `T()`, as now;
  2. sex radii: female hip 1.08, waist 0.94, chest bead at teen/adult; male shoulder 1.08, neck 1.05;
  3. build radii:
     - skinny: torso 0.85, limbs 0.82
     - athletic: shoulder/chest 1.12, waist 0.95, upper arm/thigh 1.10 (real geometry, not scale.x)
     - fat: belly bead 1.35 pushed +z, hips 1.2, upper arm 1.25, thigh 1.3, neck 1.2
- **Height in Godot:** tall 1.07, short 0.93 on bone length. Legs take 60%, torso 30%, neck 10%; the head is never scaled.
  - The child pivot offset and the piece's `Layers.scale.y` are both multiplied by s_len.
  - A 7% stretch cannot be seen at 300–450 px.
- **Node rule:** bone Node2Ds carry rotation only. Any non-uniform scale goes on their `Layers` child, never on a node with rotating children, so nothing shears.
- **Heads:** 7 variants (baby, plus f/m × child/teen/adult). They are shared across height and build.

## 3. Clothing fit
- Garments are recipes in `tools/blender/people/garments.py`, run over each body's own bead chains, so they fit all 19 shapes with no hand work:
  - `shell(chain, t0, t1, thickness, ease)`: tee 0.02, sweater 0.035, coat 0.06
  - `flare(a, b, r_top, k)`: skirt and coat tails, radius taken from the body's hip radius
  - `cap(foot, sole)`: shoes
  - `collar` / `cuff` / `hem` beads: tagged with material IDs for the mask channels
- Beads are split by body piece using t-ranges. Each split takes that piece's pivot and its overlap end beads.
- Each garment is rendered with the body as a holdout, so the inside of the garment never shows.
- Pieces per item: top 5, bottom 5, shoes 2, full-body ≤11, outerwear 5–6.
  - A skirt or long coat is an extra pelvis-bone piece and is not split between the legs.
- Height comes from bone scale, so one render serves tall and short.
- **Fit check:** `tools/fit_check.py` alpha-tests every item against every body for skin pixels poking through a covering piece. It also writes a contact sheet; the director reviews the sheets.
- Expect some per-build overrides where fat sleeves web into the chest.

## 4. Tinting
- Everything is rendered once in neutral #bdbdbd clay, with baked-AO vertex colour multiplied in.
- Texture layout (RGBA8, **lossless WebP only**, because lossy 4:2:0 smears G/B):
  - R = luminance, normalised so a lit face = 0.5
  - G = secondary mask (stripes, sole, collar, blush)
  - B = tertiary mask (or the hair grey noise)
  - A = alpha
  - Masks come from a second flat-emission material-ID pass.
- One shader, `person_clay.gdshader`, with uniforms c1, c2, c3 and boil_seed:
  ```
  base = mix(mix(c1, c2, G), c3, B)
  hl   = 0.6 * smoothstep(0.05, 0.5, luma(base))   // clamp so black stays black clay
  col  = L < 0.5 ? base*2*L : mix(base, vec3(1), (L-0.5)*2*hl)
  ```
  The clay boil (UV jitter every 2 frames) is folded into the same shader, so each sprite needs one material.
- **Skin:** about 12 tones as c1.
- **Hair:** c1 = colour, c2 = grey, and a `grey` value of 0–1 thresholds the B noise so hair greys gradually.
- **Fixed-colour decals:** eyes, mouth and tattoos use the same shader with no masks.
- **Test case:** black and navy tees must read as clay at in-room size.

## 5. Draw order and slots (z back to front, front view)
| z | Layer |
|---|---|
| 0 | hair_back, headwear_back, outer_back (hood) |
| 1 | far arm stack: skin, sleeve, outer sleeve, hand |
| 2 | far leg: skin, bottom, full-body, shoe |
| 3 | near leg (same stack) |
| 4 | pelvis skin, bottom, full-body, skirt |
| 5 | chest skin, top, full-body |
| 6 | outerwear |
| 7 | near arm stack |
| 8 | head skin, face extras |
| 9 | eyes, brows, nose, mouth |
| 10 | facial hair |
| 11 | hair_front |
| 12 | headwear_front |
| 13 | glasses |

- **Slots:** top, bottom, shoes, full-body (hides top and bottom), outerwear, headwear, glasses. No item has a sex constraint; `ages` is a content limit only.
- **Headwear `hair_mode`:** keep / hide_top / hide_all.
- **Body decals** (tattoos, scars) are children of the limb with `clip_children`, so one decal fits every body.
- **Near/far arm flags** are copied per frame from the sign of the Mixamo bone's depth.

## 6. Animation across sizes
- Pipeline: Mixamo clip → `mocap_retarget.py` → `render_cutouts.py` at 12 fps.
- `render_cutouts.py` currently stores deltas against one body's `cut_rest` (line 111), so its clips do not transfer between bodies. That changes:
  - Clips store each bone's **world direction angle**: `clips/<name>.json {fps:12, bones:{LeftArm:[deg…]}, root_y:[…], near:[…]}`.
  - At runtime: `rotation = clip_world − rest_deg[body][piece]`, composed down the chain.
- Root translation × (hip_px of this body / hip_px of the clip). Rotations change on twos.
- **Baby:** separate copied clips (crawl, sit). If none fits, ask the director; never invent angles.
- **Faces:** blink and mouth are sprite swaps.
- If a fat arm sinks into the belly, that is reported to the director. No correction is made without approval.

## 7. Asset budget (launch catalogue: 12 tops / 8 bottoms / 6 shoes / 5 full-body / 5 outerwear)
| Item | Estimate |
|---|---|
| Per body shape | ~212 pieces: skin 15, tops 60, bottoms 40, shoes 12, full-body 45, outerwear 30, extras ~10 |
| All bodies | 19 × 212 ≈ 4,000 |
| Head parts (per head, ~125) | face shapes 3, eyes 8, brows 6, mouths 4, noses 4, hair 24×2, facial hair 8, headwear 10×2, glasses 6, wrinkles 3, bald 2, freckles 3, scars 4 |
| All heads | 7 × ~125 ≈ 875 |
| **Total** | **≈ 4,900 sprites** |
| Pixels | rendered at display scale (adult ~450 px), ≈ 16 Mpx bodies + 8 Mpx heads ≈ 24 Mpx |
| Atlases | 2048², one per body shape + one per head ≈ 26 |
| Disk (estimated) | lossless WebP at ~0.8–1.2 B/px (flat masks are cheap) ≈ **20–28 MB** |
| RAM | ~4 MB per on-screen atlas, loaded lazily |
| Each new top | 19 × 5 pieces ≈ 0.4 MB |
| Render time | ~7 min per shape ≈ 2.2 h full build, incremental by hash of recipe + body parameters |

- The disk figure is an estimate; build step 7 measures it.
- Size levers if needed: split L (lossy is OK) from masks (lossless), or cap the catalogue per age.

## 8. Person look JSON (save file)
```json
{"v":1,"age":"adult","sex":"f","height":"tall","build":"fat","skin":"#c58c66",
 "head":{"face":"plain","eyes":"almond","iris":"#3b6e4a","brows":"soft","nose":"button","mouth":"smile"},
 "hair":{"cut":"bob","colour":"#4a2e1c","grey":0.2},"facial_hair":null,
 "ageing":{"wrinkles":1,"bald":0},
 "extras":[{"id":"freckles_light"},{"id":"tattoo_anchor","piece":"upper_arm_l","c":"#1d2a4a"}],
 "outfit":{"top":{"id":"tee_crew","c":["#d04040","#ffffff"]},"bottom":{"id":"jeans","c":["#3a5a8a"]},
  "shoes":{"id":"sneaker","c":["#ffffff","#222222"]},"fullbody":null,"outerwear":null,
  "headwear":null,"glasses":{"id":"round","c":["#222222"]}}}
```
- Body shape id = `age_sex_build` (baby = `baby`); height is applied at runtime.
- Supporting files: the catalogue at `data/wardrobe.json`, and one manifest per shape at `assets/people/bodies/<id>.json` (pivots, ends, rest_deg, hip_px, sprite rects).

## 9. Risks
- **Size:** lossless masks put the APK at roughly 20–28 MB; measured at step 7.
- **Voxel remesh:** can web or fuse on extreme builds and needs per-build overrides. The repo only remeshes blobs today.
- **Front view only:** no turning or side walk without doubling the art. Director decision before scaling up.
- **Rigid seams:** may show at fat elbows and shoulders on some clips; check every frame of every clip.
- **Dark tints:** may wash grey; the clamp must pass the black-tee test.
- **Hats over big hair:** may need a hair_under_hat variant per cut.
- **Determinism:** pin the Blender version.
- **Look generation:** inherited from parents + random, improved by lifestyle (GDD §10.7).

## 10. Build plan
1. **Vertical slice.** In `tools/blender/people/body.py`, build one body (child_f_skinny) as 15 pieces with pivots, plus 2 tops (tee, long-sleeve sweater) and 1 hair (front/back) as recipes. Render with masks, losslessly. Add `person_clay.gdshader` and a `Person.gd` with bone and Layers nodes. Play the wave clip as world angles with rest_deg in the bedroom at ~180 px/m, with both tops tinted 3 ways including black. Check every frame, then show the director.
2. **Prototype gate.** The same child_f in fat and athletic, at tall and short (6 bodies), with both tops and the fit check. The director decides whether the builds read.
3. All 19 body shapes (bare skin) with manifests, plus a contact sheet of all 37 at game scale.
4. Garment kit: shell, flare and cap, plus bottom, shoe, onesie and outerwear recipes. Fit check across all 19 shapes.
5. The 7 heads and their part sets. Headwear hair_mode. clip_children decals.
6. Clip library (idle, walk-in-place, sit; baby crawl/sit) with near/far flags, played on the extreme bodies with every frame checked.
7. Atlas packer (`tools/pack_atlases.py`), lossless WebP import. Measure real MB and RAM against the estimate; apply size levers if needed.
8. Load and save the look JSON, the wardrobe catalogue, wiring into `dollhouse.gd`, and resolver tests (every look resolves to existing pieces). Look generator: parents + randomness, lifestyle upgrades (GDD §10.7).
9. Fill the catalogue with incremental hashed renders. Run gdlint, gdformat and the tests, open a PR with auto-merge on green.
