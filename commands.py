import adsk.core
import adsk.fusion
import traceback
import urllib.request
import urllib.error
import json
import re
import math
import ssl  # Added for the SSL bypass

app = adsk.core.Application.get()
ui  = app.userInterface

# ── CONFIG ────────────────────────────────────────────────────────────────────
# Make sure to paste your actual Groq API key inside the quotes below!
GROQ_API_KEY = "Enter_Your_Groq_API_Key_Here"
GROQ_MODEL   = "llama-3.3-70b-versatile"
# ─────────────────────────────────────────────────────────────────────────────

CMD_ID   = "AIDesignProCommand"
CMD_NAME = "AI 3D Designer Pro"
CMD_DESC = "Advanced AI 3D design generator"

_handlers = []

# ── HELPER FUNCTIONS (injected into exec context) ─────────────────────────────

HELPER_CODE = """
import math

def get_safe_body(root, index):
    if index < 0 or index >= root.bRepBodies.count:
        return root.bRepBodies.item(root.bRepBodies.count - 1)
    return root.bRepBodies.item(index)

def make_box(root, cx, cy, cz, w, h, d, join_body=None):
    sketch = root.sketches.add(root.xYConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    lines.addTwoPointRectangle(
        adsk.core.Point3D.create(cx - w/2, cy - h/2, 0),
        adsk.core.Point3D.create(cx + w/2, cy + h/2, 0)
    )
    prof = sketch.profiles.item(0)
    extrudes = root.features.extrudeFeatures
    op = adsk.fusion.FeatureOperations.NewBodyFeatureOperation if join_body is None else adsk.fusion.FeatureOperations.JoinFeatureOperation
    ext = extrudes.createInput(prof, op)
    ext.setDistanceExtent(False, adsk.core.ValueInput.createByReal(d))
    ext.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(cz))
    extrudes.add(ext)
    return root.bRepBodies.item(root.bRepBodies.count - 1)

def make_cylinder(root, cx, cy, cz, radius, height):
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(cx, cy, 0), radius)
    prof = sketch.profiles.item(0)
    extrudes = root.features.extrudeFeatures
    ext = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext.setDistanceExtent(False, adsk.core.ValueInput.createByReal(height))
    ext.startExtent = adsk.fusion.OffsetStartDefinition.create(adsk.core.ValueInput.createByReal(cz))
    extrudes.add(ext)
    return root.bRepBodies.item(root.bRepBodies.count - 1)

def cut_cylinder(root, cx, cy, radius, height):
    sketch = root.sketches.add(root.xYConstructionPlane)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(cx, cy, 0), radius)
    prof = sketch.profiles.item(0)
    extrudes = root.features.extrudeFeatures
    ext = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
    ext.setDistanceExtent(True, adsk.core.ValueInput.createByReal(height))
    extrudes.add(ext)

def cut_box(root, cx, cy, w, h, depth):
    sketch = root.sketches.add(root.xYConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    lines.addTwoPointRectangle(
        adsk.core.Point3D.create(cx - w/2, cy - h/2, 0),
        adsk.core.Point3D.create(cx + w/2, cy + h/2, 0)
    )
    prof = sketch.profiles.item(0)
    extrudes = root.features.extrudeFeatures
    ext = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
    ext.setDistanceExtent(True, adsk.core.ValueInput.createByReal(depth))
    extrudes.add(ext)

def move_body(root, body_index, dx, dy, dz):
    body = get_safe_body(root, body_index)
    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
    transform = adsk.core.Matrix3D.create()
    transform.translation = adsk.core.Vector3D.create(dx, dy, dz)
    moveInput = root.features.moveFeatures.createInput(bodies, transform)
    root.features.moveFeatures.add(moveInput)

def rotate_body(root, body_index, angle_deg, px=0, py=0, pz=0):
    body = get_safe_body(root, body_index)
    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
    transform = adsk.core.Matrix3D.create()
    transform.setToRotation(math.radians(angle_deg), adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(px, py, pz))
    moveInput = root.features.moveFeatures.createInput(bodies, transform)
    root.features.moveFeatures.add(moveInput)

def copy_and_rotate(root, body_index, angle_deg, px=0, py=0, pz=0):
    body = get_safe_body(root, body_index)
    bodies = adsk.core.ObjectCollection.create()
    bodies.add(body)
    transform = adsk.core.Matrix3D.create()
    transform.setToRotation(math.radians(angle_deg), adsk.core.Vector3D.create(0, 0, 1), adsk.core.Point3D.create(px, py, pz))
    moveInput = root.features.moveFeatures.createInput(bodies, transform)
    moveInput.isCopy = True
    root.features.moveFeatures.add(moveInput)
"""

SYSTEM_PROMPT = """You are a Fusion 360 Python API expert.
Return ONLY raw Python code. No markdown, no backticks, no explanation.

UNITS: All values in CENTIMETERS. Divide mm by 10.
10mm=1.0  20mm=2.0  50mm=5.0  100mm=10.0  150mm=15.0  200mm=20.0

ALWAYS START WITH:
app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent

YOU HAVE THESE HELPER FUNCTIONS AVAILABLE (use them instead of raw API):

make_cylinder(root, cx, cy, cz, radius, height)
  - Creates a cylinder at position (cx,cy), starting at height cz, with given radius and height
  - Returns the body

cut_cylinder(root, cx, cy, radius, height)
  - Cuts a cylindrical hole through existing bodies

make_box(root, cx, cy, cz, w, h, d, join_body=None)
  - Creates a box centered at (cx,cy), starting at cz, with width w, depth h, height d
  - Returns the body

cut_box(root, cx, cy, w, h, depth)
  - Cuts a rectangular hole through existing bodies

move_body(root, body_index, dx, dy, dz)
  - Moves body at index by (dx,dy,dz)

rotate_body(root, body_index, angle_deg, px=0, py=0, pz=0)
  - Rotates body around Z axis by angle_deg degrees around point (px,py,pz)

copy_and_move(root, body_index, dx, dy, dz)
  - Copies body and moves copy by (dx,dy,dz)

copy_and_rotate(root, body_index, angle_deg, px=0, py=0, pz=0)
  - Copies body and rotates copy around Z axis

QUADCOPTER DRONE EXAMPLE (200mm body, 120mm arms, 30mm motor mounts):
app = adsk.core.Application.get()
design = adsk.fusion.Design.cast(app.activeProduct)
root = design.rootComponent
# 1. Center plate 200x200x15mm
make_cylinder(root, 0, 0, 0, 10.0, 1.5)
# 2. Cut center hole 50mm
cut_cylinder(root, 0, 0, 2.5, 1.5)
# 3. One arm 120x20x8mm along X axis
make_box(root, 6.0, 0, 0, 12.0, 2.0, 0.8)
# 4. Copy arm rotated to all 4 diagonal positions
copy_and_rotate(root, 1, 45)
copy_and_rotate(root, 1, 90)
copy_and_rotate(root, 1, 135)
copy_and_rotate(root, 1, 180)
# 5. Motor mount at arm end
make_cylinder(root, 12.0, 0, 0, 1.5, 0.8)
# 6. Copy motor mounts to all arms
copy_and_rotate(root, 5, 45)
copy_and_rotate(root, 5, 90)
copy_and_rotate(root, 5, 135)
copy_and_rotate(root, 5, 180)

RULES:
- Use helper functions, NOT raw Fusion 360 API calls
- Never use moveFeatures.createInput directly
- Never use sketchLines or sketchCircles directly
- Always use cm units
- body_index counts from 0, increments with each new body created
# Add this line to your RULES section in the SYSTEM_PROMPT string:
- IMPORTANT: When making arms, ensure the 'cx' (center X) is half the width of the arm plus the radius of the center plate so they don't overlap.
"""


def call_groq(prompt):
    payload = json.dumps({
        "model": GROQ_MODEL,
        "max_tokens": 4096,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                "Create this 3D design using ONLY the helper functions provided. "
                "Do NOT use raw Fusion 360 API. Use cm units only. "
                "Request: " + prompt
            )}
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

    # --- SSL BYPASS ADDED HERE ---
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        # Added the context=ctx parameter to bypass Fusion's strict SSL checks
        with urllib.request.urlopen(req, timeout=90, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError("HTTP {}: {}".format(e.code, error_body))

    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        raise RuntimeError("Unexpected response:\n" + json.dumps(data, indent=2))


def clean_code(raw):
    raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw.strip())
    raw = re.sub(r"\n?```$", "", raw.strip())
    return raw.strip()


def run_generated_code(code):
    exec_globals = {"adsk": adsk, "math": math, "app": app}
    # First inject helpers
    exec(HELPER_CODE, exec_globals)
    # Then run generated code
    exec(code, exec_globals)


class AIDesignCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            inputs = cmd.commandInputs

            inputs.addTextBoxCommandInput(
                "title_box", "",
                "<b>AI 3D Designer Pro</b><br>"
                "<small>Describe your design with dimensions in mm.</small>",
                2, True
            )
            inputs.addStringValueInput("prompt_input", "Design prompt", "")

            complexity_input = inputs.addDropDownCommandInput(
                "complexity_input", "Complexity",
                adsk.core.DropDownStyles.TextListDropDownStyle
            )
            complexity_input.listItems.add("Simple (single body)", True)
            complexity_input.listItems.add("Medium (multiple bodies)", False)
            complexity_input.listItems.add("Complex (full assembly like drone)", False)

            inputs.addTextBoxCommandInput(
                "tip_box", "",
                "<small>Tip: For drones select Complex and include all dimensions.</small>",
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
            inputs     = args.command.commandInputs
            prompt     = inputs.itemById("prompt_input").value.strip()
            complexity = inputs.itemById("complexity_input").selectedItem.name

            if not prompt:
                ui.messageBox("Please enter a design prompt.")
                return

            full_prompt = "Design: {}\nComplexity: {}\nUse helper functions only.".format(
                prompt, complexity
            )

            progress = ui.createProgressDialog()
            progress.isCancelButtonShown = False
            progress.show("AI 3D Designer Pro", "Generating design with AI...", 0, 4, False)
            progress.progressValue = 1

            raw_code = call_groq(full_prompt)
            code = clean_code(raw_code)

            progress.message = "Building in Fusion 360..."
            progress.progressValue = 3

            run_generated_code(code)

            progress.progressValue = 4
            progress.hide()

            ui.messageBox("Design created!\n\nPrompt: {}\n\nCode:\n{}".format(prompt, code))

        except RuntimeError as e:
            try: progress.hide()
            except: pass
            ui.messageBox("API Error:\n{}".format(str(e)))
        except Exception:
            try: progress.hide()
            except: pass
            ui.messageBox("Fusion 360 Error:\n" + traceback.format_exc())


def start():
    cmd_defs = ui.commandDefinitions
    existing = cmd_defs.itemById(CMD_ID)
    if existing:
        existing.deleteMe()

    cmd_def = cmd_defs.addButtonDefinition(CMD_ID, CMD_NAME, CMD_DESC)
    on_created = AIDesignCommandCreatedHandler()
    cmd_def.commandCreated.add(on_created)
    _handlers.append(on_created)

    solid_tab = ui.allToolbarTabs.itemById("SolidTab")
    create_panel = solid_tab.toolbarPanels.itemById("SolidCreatePanel")
    create_panel.controls.addCommand(cmd_def)

    ui.messageBox("AI 3D Designer Pro loaded!\nSOLID tab -> CREATE panel")


def stop():
    try:
        solid_tab = ui.allToolbarTabs.itemById("SolidTab")
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
