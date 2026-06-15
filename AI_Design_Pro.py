import adsk.core
import adsk.fusion
import traceback
from . import commands

def run(context):
    try:
        commands.start()
    except:
        adsk.core.Application.get().userInterface.messageBox(
            'Failed to start:\n{}'.format(traceback.format_exc())
        )

def stop(context):
    try:
        commands.stop()
    except:
        adsk.core.Application.get().userInterface.messageBox(
            'Failed to stop:\n{}'.format(traceback.format_exc())
        )
