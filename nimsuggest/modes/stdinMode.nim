import tables, net, parseopt2, strutils, rdstdin
import ../nimsuggest, commonMode
import compiler/msgs


const stdinModeHelpMsg = """
Nimsuggest Stdin Mode Switches:
  -i, --interactive:[true|false]
          Run in interactive mode, suitable for terminal use.       
"""

const interactiveHelpMsg = """
Usage: sug|con|def|use|dus|chk|highlight|outline file.nim[;dirtyfile.nim]:line:col
Type 'quit' to quit, 'debug' to toggle debug mode on/off, and 'terse'
to toggle terse mode on/off.
"""


type StdinModeData = ref object of ModeData
  interactive: bool


proc initializeData*(): ModeData =
  var res = new(StdinModeData)
  result = ModeData(res)

proc addModes*(modes: TableRef[string, ModeInitializer]) =
  modes["stdin"] = initializeData


# ModeData Interface Methods
method processSwitches(data: StdinModeData, switches: SwitchSequence) =
  for switch in switches:
    case switch.kind
    of cmdLongOption, cmdShortOption:
      case switch.key.normalize
      of "interactive", "i":
        if switch.value == "":
          data.interactive = true
        else:
          try:
            data.interactive = parseBool(switch.value)
          except ValueError:
            quit("Invalid \"interactive\" value \"" & switch.value & "\"")
      else:
        echo("Invalid mode switch \"$#:$#\"" % [switch.key, switch.value])
        quit()
    else:
      discard

method echoOptions(data: StdinModeData) =
  echo(stdinModeHelpMsg)
  quit()

method mainCommand(data: StdinModeData) =
  msgs.writelnHook = (proc (msg: string) = echo msg)
  let prefix = if data.interactive: "> " else: ""
  if data.interactive:
    echo("Running Nimsuggest Stdin Mode")
    echo("Project file: \"$#\"" % [data.projectPath])
    echo interactiveHelpMsg

  var line = ""
  while readLineFromStdin(prefix, line):
    flushFile(stdin)
    parseCmdLine line
    echo("\n")
    flushFile(stdout)