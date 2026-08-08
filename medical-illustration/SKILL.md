---
name: medical-illustration
description: "Create medical/healthcare educational illustrations and comic-style storyboard panels. Handles script-to-panel conversion, character consistency, and fallback when image_gen is unavailable."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [medical, illustration, comic, storyboard, healthcare, education, AI-image]
    related: [baoyu-infographic, excalidraw, ascii-art]
---

# Medical Illustration & Comic Panel Creator

Create medical/healthcare educational illustrations and comic-style storyboard panels. Covers:

- **Medical comic storyboard** — convert educational scripts into panel-by-panel comic format (character descriptions, scene composition, dialogue bubbles, visual hierarchy)
- **Individual panel illustration** — generate or describe individual illustration panels
- **Fallback workflows** — when image_gen API is unavailable (no API key, service down), produce SVG vector illustrations, SVG anatomy diagrams, ASCII concept sketches, or detailed spec sheets for human artists

## When to Use

- User asks for medical/healthcare educational illustrations, comic panels, or infographic images
- User provides a script and wants it converted to a visual comic/storyboard format
- User wants character-consistent illustrations across multiple panels
- User has an education script (patient education, clinical training) that needs visual treatment

## Workflow

### Phase 1: Script Analysis & Panel Layout

1. **Identify core message** per section — each section should map to 1-3 panels max
2. **Define characters** — give each character a consistent description used across all panels:
   - Name, age, gender, role (patient/nurse/doctor)
   - Clothing (hospital gown colors, nurse uniform style)
   - Distinguishing features (hair, glasses)
   - Use this description in EVERY image generation prompt for consistency
3. **Map sections to panels** — create a panel list with:
   - Panel number and name
   - Scene description (setting, lighting, composition)
   - Character positions and poses
   - Dialogue/text in bubble or caption
   - Visual emphasis (what should the viewer look at first)
   - Aspect ratio (wide for group scenes, portrait for single figure, etc.)

### Phase 2: Generate the Panels

#### Option A: AI Image Generation (preferred)

If `image_generate` is available and configured:

1. Write a detailed prompt for each panel, including:
   - Style keyword (start with a style the user likes)
   - Character descriptions (verbatim from Phase 1)
   - Scene setting and composition
   - Action/pose description
   - Text overlay needs (note that AI may not render text well — plan to add text in post)
2. Generate panels sequentially or in small batches (2-4 at a time)
3. Save each image to a named file in an output directory

#### Option B: SVG Vector Illustration

If `image_generate` is unavailable, generate clean SVG medical illustrations:

- Use simple geometric shapes for characters
- Clear labels and arrows for anatomical/educational content
- Consistent color palette per panel
- Export as standalone `.svg` files

#### Option C: Detailed Spec Sheet for Human Artist

If neither AI nor SVG is suitable, produce a professional-grade panel spec:

- Full panel layout description (composition, angles, framing)
- Exact character descriptions for artist reference
- Dialogue bubble placement instructions
- Color palette codes (HEX)
- Recommended aspect ratios
- Save as `.md` file in output directory

### Phase 3: Output Organization

```
illustrations/{topic-slug}/
├── panels/
│   ├── panel-01-intro.svg or .png
│   ├── panel-02-pain-scale.svg or .png
│   └── ...
├── storyboard.md          — Full panel-by-panel layout
├── character-sheet.md     — Character reference for consistency
└── README.md              — Overview and instructions
```

## Fallback Decision Tree

```
Can I generate images? (image_generate tool works)
├── YES → Generate panels as PNG/JPG
└── NO → Do I have SVG tools? (can write SVG files)
    ├── YES → Create SVG illustrations
    └── NO → Produce detailed spec sheet for human artist
```

## Medical Comic Style Guidelines

- **Characters**: Simple, friendly, recognizable. Avoid photorealistic — stylized is better for education.
- **Colors**: Warm, approachable palette. Use blues/greens for medical trust, warm tones for comfort.
- **Text**: Keep dialogue concise. Use speech bubbles or caption boxes. Note: AI text rendering is unreliable — always plan to add text in post.
- **Anatomy**: Show enough for clarity but avoid gore or distressing imagery.
- **Perspective**: Eye-level or slightly above for patient scenes. Close-up for pain score/rating scenes.
- **Panel flow**: Read left-to-right (for Western audiences) or right-to-left (for Japanese manga style — ask the user).

## Character Consistency Tips

When generating multiple panels with the same character:

1. **Reuse exact character descriptions** in every prompt — same clothing, hair, accessories
2. **Use a seed** if the image generation tool supports it (save the seed in character-sheet.md)
3. **Generate a character reference sheet** first — front view + side view if possible
4. **Keep backgrounds simple** so character is the focus
5. If styles vary between panels, add explicit style references to each prompt (e.g., "same art style as previous panels")

## Pitfalls

1. **Text in AI-generated images is unreliable** — never rely on AI to render Chinese/English text in panels. Always plan to add text overlays with a tool like Canva, Figma, or SVG text.
2. **Character drift** — if generating multiple panels, character appearance will drift. Always include the full character description in every prompt.
3. **Complex medical scenes don't render well** — keep scenes to 1-2 characters max for AI generation. Complex multi-character scenes should be SVG or spec-sheet only.
4. **Don't generate more than 6 panels in one session** — this gets expensive and repetitive. Stick to the most important panels.
5. **Verify each panel before generating more** — make sure style and quality match before committing to the full set.

## References

- `references/case-medical-osteoporosis-pain.md` — 完整18格分镜案例（骨质疏松性骨折疼痛管理漫画），展示从脚本到分镜的转化方法
