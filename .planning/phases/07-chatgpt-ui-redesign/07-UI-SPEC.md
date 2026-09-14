# UI Specification: Phase 7 — ChatGPT-Style Minimalist UI & Streamlined Interaction

## 1. Vision & Architecture
AskDoc AI's user experience is refined to mirror the minimalist, high-focus interface of modern AI chat applications (like ChatGPT and Gemini). The interface eliminates redundant visual elements, removes clutter, unifies file upload into the sidebar with an intuitive click-to-browse card, places speech input directly into the chat input bar, enables per-message audio playback, and delivers an interactive single-visit onboarding walkthrough.

---

## 2. Layout Structure & Color Tokens

### 2.1 Color Palette (ChatGPT Dark Theme)
- **Primary Background**: `#212121` (Dark matte charcoal)
- **Sidebar Background**: `#171717` (Deep charcoal)
- **Card / Bubble Background**: `#2f2f2f` (Soft elevated gray)
- **Chat Input Background**: `#2f2f2f` (Container matching ChatGPT pill)
- **Border Subtle**: `rgba(255, 255, 255, 0.08)`
- **Border Active/Hover**: `rgba(255, 255, 255, 0.20)`
- **Text Primary**: `#ececec`
- **Text Secondary / Muted**: `#b4b4b4`
- **Accent Glow**: `#10a37f` (ChatGPT emerald) or `#38bdf8` (Ice sky blue)
- **Destructive**: `#ef4444` (Soft crimson for file deletion)

### 2.2 Typography & Iconography
- **Font**: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif.
- **Icon Policy**: No cartoon or colorful emoji sets. All action icons are clean monochrome SVG paths or crisp unicode symbols (`✕`, `↑`, `▶`, `■`, `●`, `☊`, `⌫`).

---

## 3. Component Hierarchy

### 3.1 Sidebar ("Add Files" & Active Session Documents)
- **Header**: `Add Files` with file format pills (`PDF`, `DOCX`, `PNG`, `JPG`, `CSV`, `JSON`, `HTML`).
- **Interactive Dropzone Card**:
  - Dark container with subtle dashed border (`1.5px dashed rgba(255, 255, 255, 0.15)`).
  - Title: "Click to upload or drop files".
  - Subtitle: "PDF, Images, Office Docs, Data files".
  - Button pill: "Browse files" with upload symbol.
  - Clicking anywhere inside triggers the system file manager (`file_uploader`).
- **Session Documents List**:
  - Title: `Active Documents (N)`
  - Each item displays:
    - Format indicator badge (e.g. `[PDF]`, `[IMG]`, `[DOC]`).
    - Filename (truncated if long).
    - File size.
    - Delete button (`✕`) on the right:
      - Clicking prompts or executes deletion via `DELETE /documents/{filename}`.
      - Rebuilds vector store and refreshes file list.
- **Footer**:
  - `Clear Chat` (`⌫`) button.
  - `Guide / Tutorial` (`?`) button to re-trigger the walkthrough modal.

### 3.2 Main Viewport (ChatGPT Conversation Stream)
- **Top Bar**: Minimalist header showing `AskDoc AI` title + small count badge of loaded documents (`N documents active`).
- **Chat Stream**:
  - User messages: right-aligned or crisp `#2f2f2f` bubble.
  - Assistant messages: clean left-aligned text with markdown formatting, tables, lists, and code blocks.
  - **Sources Expander**: Compact, subtle fold-out listing source document names and page numbers.
  - **ChatGPT Action Row** (at bottom of assistant message):
    - `🔊 Listen` (or sound icon): Triggers per-response Text-to-Speech audio generation and plays the response in place.
    - `📋 Copy`: Copies answer text to clipboard.
- **Chat Input Bar (Bottom Centered)**:
  - Floating pill container (`max-width: 768px`) with rounded border radius (`24px`).
  - Textarea: "Ask a question about your documents...".
  - Action buttons inside the right edge of the pill:
    - **Microphone Button** (positioned immediately on the LEFT of the Send button):
      - Icon: Clean microphone SVG.
      - Idle: Subtle white/gray icon.
      - Listening: Pulsing red active ring (`#ef4444`).
      - Click: Toggles speech recognition. When speech finishes, populates text and auto-sends.
    - **Send Button**:
      - Circular upward arrow (`↑`) button.
      - Active when text is present.

### 3.3 Interactive Modern Site Tutorial (One-time Walkthrough)
- Multi-step interactive modal or spotlight overlay:
  - **Step 1: Upload Documents** — Highlights the sidebar upload card. Explains multi-format ingestion (PDF, Images with Vision OCR, Office, CSV, JSON).
  - **Step 2: Ask or Speak** — Highlights the chat input bar and the microphone button next to Send.
  - **Step 3: Grounded Answers & Voice Playback** — Explains strict anti-hallucination citations and the per-response Listen audio button.
- Controls: "Back", "Next", "Get Started", "Skip".
- Persistence: Stored in browser `localStorage.getItem("antirag_tour_seen")`. If set, never pops up again on refresh unless explicitly launched via the sidebar Guide button.

---

## 4. Deletions & Cleanups (From Red-Marked Screenshot)
1. **Remove**: Bulky floating bottom `🎙️ Voice Question` audio recorder bar above the chat input.
2. **Remove**: Sidebar `Audio & Settings` toggle `🔊 Speak responses (Voice Output)`.
3. **Remove**: Main chat screen duplicated upload box.
