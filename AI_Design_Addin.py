import adsk.core
import adsk.fusion
import traceback
from . import commands

def run(context):
    try:
        commands.start()
    except:
        adsk.core.Application.get().userInterface.messageBox(
            'Failed to start AI Design Add-in:\n{}'.format(traceback.format_exc())
        )

def stop(context):
    try:
        commands.stop()
    except:
        adsk.core.Application.get().userInterface.messageBox(
            'Failed to stop AI Design Add-in:\n{}'.format(traceback.format_exc())
        )
