import adsk.core
import adsk.fusion
import traceback
import urllib.request
import urllib.error
import json
import re

app = adsk.core.Application.get()
ui  = app.userInterface

# ── CONFIG ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = "enter you API key here"
GROQ_MODEL   = "llama-3.3-70b-versatile"
# ─────────────────────────────────────────────────────────────────────────────

CMD_ID   = "AIDesignGroqCommand"
CMD_NAME = "AI 3D Designer"
CMD_DESC = "Generate 3D designs from natural language prompts using Groq AI (Free)"

_handlers = []

SYSTEM_PROMPT = """You are an expert Autodesk Fusion 360 Python API developer.
When the user describes a 3D object, return ONLY raw executable Python code.
No markdown, no triple backticks, no explanation, no comments whatsoever.

CRITICAL API RULES - these are the ONLY correct methods:
- Circles: sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius)   # NOT .add()
- Lines rectangle: sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)
- Single line: sketch.sketchCurves.sketchLines.addByTwoPoints(p1, p2)
- Extrude: root.features.extrudeFeatures
- Revolve: root.features.revolveFeatures
- All units in CM (divide mm by 10): 50mm = 5.0, 100mm = 10.0, 25mm = 2.5
- adsk is already imported - do NOT import it
- First line must be: app = adsk.core.Application.get()
- Always: design = adsk.fusion.Design.cast(app.activeProduct)
- Always: root = design.rootComponent

CORRECT EXAMPLES:

# Draw a circle center (0,0,0) radius 1cm:
center = adsk.core.Point3D.create(0, 0, 0)
sketch.sketchCurves.sketchCircles.addByCenterRadius(center, 1.0)

# Draw rectangle from origin to (5,3):
sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create(0,0,0),
    adsk.core.Point3D.create(5,3,0)
)

# Extrude profile by 2cm:
extInput = root.features.extrudeFeatures.createInput(
    prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
)
extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.0))
root.features.extrudeFeatures.add(extInput)

# Cut a hole (use CutFeatureOperation):
extInput = root.features.extrudeFeatures.createInput(
    prof, adsk.fusion.FeatureOperations.CutFeatureOperation
)
extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.0))
root.features.extrudeFeatures.add(extInput)

FULL EXAMPLE - box 50mm x 30mm x 20mm:
app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent
sketch = root.sketches.add(root.xYConstructionPlane)
sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0,0,0), adsk.core.Point3D.create(5,3,0))
prof = sketch.profiles.item(0)
extInput = root.features.extrudeFeatures.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(2.0))
root.features.extrudeFeatures.add(extInput)

FULL EXAMPLE - cylinder radius 20mm height 40mm:
app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent
sketch = root.sketches.add(root.xYConstructionPlane)
sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0,0,0), 2.0)
prof = sketch.profiles.item(0)
extInput = root.features.extrudeFeatures.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(4.0))
root.features.extrudeFeatures.add(extInput)"""


def call_groq(prompt):
    payload = json.dumps({
        "model": GROQ_MODEL,
        "max_tokens": 2048,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": "Create this 3D object in Fusion 360: " + prompt}
        ]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": "Bearer {}".format(GROQ_API_KEY.strip()),
            "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError("HTTP {}: {}".format(e.code, error_body))

    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        raise RuntimeError("Unexpected Groq response:\n" + json.dumps(data, indent=2))


def clean_code(raw):
    raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw.strip())
    raw = re.sub(r"\n?```$",           "", raw.strip())
    return raw.strip()


def run_generated_code(code):
    exec_globals = {"adsk": adsk}
    exec(code, exec_globals)


class AIDesignCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd    = args.command
            cmd.isRepeatable = False
            inputs = cmd.commandInputs
            inputs.addTextBoxCommandInput(
                "title_box", "",
                "<b>AI 3D Designer</b> powered by Groq<br>"
                "<small>Describe the object you want to create and click OK.</small>",
                2, True
            )
            inputs.addStringValueInput("prompt_input", "Describe object", "")
            inputs.addTextBoxCommandInput(
                "status_box", "Status",
                "Ready - enter a prompt and click OK.",
                2, True
            )
            on_exec = AIDesignExecuteHandler()
            cmd.execute.add(on_exec)
            _handlers.append(on_exec)
        except:
            ui.messageBox("Error:\n" + traceback.format_exc())


class AIDesignExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            inputs = args.command.commandInputs
            prompt = inputs.itemById("prompt_input").value.strip()
            if not prompt:
                ui.messageBox("Please enter a prompt first.")
                return

            progress = ui.createProgressDialog()
            progress.isCancelButtonShown = False
            progress.show("AI 3D Designer", "Asking Groq AI...", 0, 3, False)
            progress.progressValue = 1

            raw_code = call_groq(prompt)
            code     = clean_code(raw_code)

            progress.message       = "Running generated code..."
            progress.progressValue = 2

            run_generated_code(code)

            progress.progressValue = 3
            progress.hide()

            ui.messageBox("Design created!\n\nPrompt: {}\n\nCode:\n{}" .format(prompt, code))

        except RuntimeError as e:
            try: progress.hide()
            except: pass
            ui.messageBox("API Error:\n{}\n\nCheck your API key in commands.py".format(str(e)))
        except Exception:
            try: progress.hide()
            except: pass
            ui.messageBox("Error:\n" + traceback.format_exc())


def start():
    cmd_defs = ui.commandDefinitions
    existing = cmd_defs.itemById(CMD_ID)
    if existing:
        existing.deleteMe()

    cmd_def    = cmd_defs.addButtonDefinition(CMD_ID, CMD_NAME, CMD_DESC)
    on_created = AIDesignCommandCreatedHandler()
    cmd_def.commandCreated.add(on_created)
    _handlers.append(on_created)

    solid_tab    = ui.allToolbarTabs.itemById("SolidTab")
    create_panel = solid_tab.toolbarPanels.itemById("SolidCreatePanel")
    create_panel.controls.addCommand(cmd_def)

    ui.messageBox("AI 3D Designer (Groq) loaded!\nFind the button in: SOLID tab -> CREATE panel")


def stop():
    try:
        solid_tab    = ui.allToolbarTabs.itemById("SolidTab")
        create_panel = solid_tab.toolbarPanels.itemById("SolidCreatePanel")
        ctrl = create_panel.controls.itemById(CMD_ID)
        if ctrl:
            ctrl.deleteMe()
        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if cmd_def:
            cmd_def.deleteMe()
        _handlers.clear()
    except:
        pass
