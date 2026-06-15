# AI 3D Designer for Fusion 360 🤖✨

Turn plain English into 3D models — right inside Autodesk Fusion 360.

This add-in lets you type a description like *"a cylinder 20mm radius and 40mm height"* or *"a 50x30x20mm box with a 10mm hole through the center"*, and it uses [Groq](https://groq.com/) (free, ultra-fast LLM inference) to generate and execute the Fusion 360 Python API code on the spot.

---

## ✨ Features

- 🗣️ **Natural language to CAD** — describe what you want, get a 3D model
- ⚡ **Powered by Groq** — fast, free-tier LLM inference (`llama-3.3-70b-versatile`)
- 🧩 **Seamless integration** — adds a button directly to the **SOLID → CREATE** panel
- 🔍 **Transparent** — shows you the generated Python code after every run
- 🆓 **No paid API required** — works with Groq's free API tier

---

## 📋 Requirements

- Autodesk Fusion 360 (Windows or macOS)
- A free [Groq API key](https://console.groq.com/keys)
- Internet connection (to call the Groq API)

---

## 🚀 Installation

1. **Download or clone this repository**

   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git
   ```

2. **Locate your Fusion 360 Add-Ins folder**

   - **Windows:**
     `%appdata%\Autodesk\Autodesk Fusion 360\API\AddIns`
   - **macOS:**
     `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns`

3. **Copy the project folder** (containing `AI_Design_Addin.py`, `AI_Design_Addin.manifest`, and `commands.py`) into the `AddIns` folder above.

4. **Add your Groq API key** — open `commands.py` and replace:

   ```python
   GROQ_API_KEY = "enter you API key here"
   ```

   with your actual key from [console.groq.com/keys](https://console.groq.com/keys):

   ```python
   GROQ_API_KEY = "gsk_your_actual_key_here"
   ```

5. **Load the add-in in Fusion 360**

   - Open Fusion 360
   - Go to **Utilities → Add-Ins → Scripts and Add-Ins** (or press `Shift + S`)
   - Under the **Add-Ins** tab, find **AI_Design_Addin**
   - Click **Run** (optionally check **Run on Startup**)

---

## 🛠️ Usage

1. Switch to the **Design** workspace
2. Go to the **SOLID** tab → **CREATE** panel
3. Click **AI 3D Designer**
4. Type a description of the object you want, e.g.:
   - `a box 50mm x 30mm x 20mm`
   - `a cylinder with radius 20mm and height 40mm`
   - `a 60mm cube with a 15mm hole through the top`
5. Click **OK** and watch it appear in the design

A dialog will show the generated code so you can review or reuse it.

---

## ⚙️ Configuration

| Setting | Location | Description |
|---|---|---|
| `GROQ_API_KEY` | `commands.py` | Your Groq API key (required) |
| `GROQ_MODEL` | `commands.py` | Model used for generation (default: `llama-3.3-70b-versatile`) |

---

## ⚠️ Important Notes

- **Keep your API key private.** Never commit your real API key to a public repository. Consider using an environment variable or a separate untracked config file for production use.
- **Generated code is executed directly** via Python's `exec()`. Only use prompts you trust, and review the generated code shown in the result dialog.
- Results depend on the quality of the AI model's response — complex or ambiguous prompts may produce unexpected geometry.

---

## 🧰 Project Structure

```
AI_Design_Addin/
├── AI_Design_Addin.py        # Add-in entry point (run/stop)
├── AI_Design_Addin.manifest  # Fusion 360 add-in manifest
└── commands.py                # Core logic: UI, Groq API calls, code execution
```

---

## 🤝 Contributing

Pull requests, issue reports, and feature suggestions are welcome! Feel free to fork the repo and submit improvements.

---

## 📄 License

This project is open source. Add your preferred license (e.g. MIT) here.

---

## 🙏 Acknowledgements

- [Groq](https://groq.com/) for free, blazing-fast LLM inference
- Autodesk Fusion 360 API documentation
