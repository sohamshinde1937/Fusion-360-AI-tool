# AI 3D Designer Pro 🤖🛠️

An advanced AI-powered add-in for Autodesk Fusion 360 that turns natural language design descriptions into real, multi-part 3D models — including complex assemblies like quadcopter drones.

This is the **Pro** version, built on top of a helper-function framework that lets the AI compose primitives (boxes, cylinders, cuts, copies, rotations) into structured assemblies, instead of writing raw, error-prone Fusion 360 API calls.

---

## ✨ Features

- 🗣️ **Natural language → 3D assembly** — describe a design with dimensions in mm and get a working model
- 🧩 **Helper-function framework** — AI composes designs using safe, pre-built functions (`make_box`, `make_cylinder`, `cut_cylinder`, `move_body`, `rotate_body`, `copy_and_rotate`, etc.)
- 🎛️ **Complexity selector** — choose Simple, Medium, or Complex (full assembly) generation modes
- ⚡ **Powered by Groq** — fast, free-tier LLM inference (`llama-3.3-70b-versatile`)
- 🚁 **Built-in drone example** — the AI is primed with a full quadcopter drone build pattern (center plate, arms, motor mounts)
- 🔍 **Transparent** — shows the generated code after every run

---

## 📋 Requirements

- Autodesk Fusion 360 (Windows or macOS)
- A free [Groq API key](https://console.groq.com/keys)
- Internet connection (to call the Groq API)

---

## 🚀 Installation

1. **Download or clone this repository**

   ```bash
   git clone https://github.com/sohamshinde1937/Fusion-360-AI-tool.git
   ```

2. **Locate your Fusion 360 Add-Ins folder**

   - **Windows:**
     `%appdata%\Autodesk\Autodesk Fusion 360\API\AddIns`
   - **macOS:**
     `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns`

3. **Copy the project folder** (containing `AI_Design_Pro.py`, `AI_Design_Pro.manifest`, and `commands.py`) into the `AddIns` folder above.

4. **Add your Groq API key** — open `commands.py` and replace:

   ```python
   GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"
   ```

   with your actual key from [console.groq.com/keys](https://console.groq.com/keys).

  

5. **Load the add-in in Fusion 360**

   - Open Fusion 360
   - Go to **Utilities → Add-Ins → Scripts and Add-Ins** (or press `Shift + S`)
   - Under the **Add-Ins** tab, find **AI_Design_Pro**
   - Click **Run** (optionally check **Run on Startup**)

---

## 🛠️ Usage

1. Switch to the **Design** workspace
2. Go to the **SOLID** tab → **CREATE** panel
3. Click **AI 3D Designer Pro**
4. Enter a design prompt with dimensions in **mm**, e.g.:
   - `a 60mm cube with a 20mm hole through the center`
   - `a cylinder 40mm radius and 80mm height with a 10mm hole through it`
   - `a quadcopter drone with a 200mm body, 120mm arms, and 30mm motor mounts`
5. Select a **Complexity** level:
   - **Simple** – single body
   - **Medium** – multiple bodies
   - **Complex** – full assembly (e.g. drone)
6. Click **OK**

A dialog will show the generated code after the model is built.

---

## 🧠 How It Works

Instead of letting the AI write raw, error-prone Fusion 360 API calls, this add-in injects a library of **helper functions** into the execution environment. The AI is instructed to compose designs using only these functions:

| Function | Description |
|---|---|
| `make_box(root, cx, cy, cz, w, h, d, join_body=None)` | Creates a box centered at (cx, cy), starting at height cz |
| `make_cylinder(root, cx, cy, cz, radius, height)` | Creates a cylinder at (cx, cy), starting at height cz |
| `cut_cylinder(root, cx, cy, radius, height)` | Cuts a cylindrical hole through existing bodies |
| `cut_box(root, cx, cy, w, h, depth)` | Cuts a rectangular hole through existing bodies |
| `move_body(root, body_index, dx, dy, dz)` | Moves a body by an offset |
| `rotate_body(root, body_index, angle_deg, px, py, pz)` | Rotates a body around the Z axis |
| `copy_and_rotate(root, body_index, angle_deg, px, py, pz)` | Copies a body and rotates the copy |

All dimensions are handled in **centimeters internally** (the AI converts from mm), and `body_index` increments with each new body created — letting the AI reference earlier parts for copies, moves, and rotations.

---

## ⚙️ Configuration

| Setting | Location | Description |
|---|---|---|
| `GROQ_API_KEY` | `commands.py` | Your Groq API key (required) |
| `GROQ_MODEL` | `commands.py` | Model used for generation (default: `llama-3.3-70b-versatile`) |

---

## ⚠️ Important Notes

- **Keep your API key private.** Never commit your real key to a public repository.
- **Generated code is executed directly** via Python's `exec()`. Only use prompts you trust, and review the generated code shown in the result dialog.
- This version disables SSL certificate verification (`ssl.CERT_NONE`) for the Groq API request to work around Fusion 360's bundled Python environment. This reduces transport security — use with awareness, and consider replacing it with a proper certificate bundle if you need stronger guarantees.
- Results depend on the AI model's interpretation of your prompt — be specific about dimensions and layout for best results.

---

## 🧰 Project Structure

```
AI_Design_Pro/
├── AI_Design_Pro.py        # Add-in entry point (run/stop)
├── AI_Design_Pro.manifest   # Fusion 360 add-in manifest
└── commands.py               # Core logic: UI, helper functions, Groq API calls, execution
```

---

## 🤝 Contributing

Pull requests, issue reports, and feature suggestions are welcome! Ideas for new helper functions (fillets, patterns, threads, etc.) are especially appreciated.

---

## 📄 License

MIT License

Copyright (c) 2026 sohamshinde1937

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 🙏 Acknowledgements

- [Groq](https://groq.com/) for free, blazing-fast LLM inference
- Autodesk Fusion 360 API documentation
