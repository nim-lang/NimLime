#
#
#           The Nim Compiler
#        (c) Copyright 2015 Andreas Rumpf
#
#    See the file "copying.txt", included in this
#    distribution, for details about the copyright.
#

## Nimsuggest is a tool that helps to give editors IDE like capabilities.
import tables, parseopt2, strutils, os, parseutils, sequtils, net, rdstdin, sexp

import compiler/options, compiler/commands, compiler/modules, compiler/sem,
  compiler/passes, compiler/passaux, compiler/msgs, compiler/nimconf,
  compiler/extccomp, compiler/condsyms, compiler/lists,
  compiler/sigmatch, compiler/ast

const 
  nimsuggestVersion = "0.1.0"
  helpMsg = """
Nimsuggest - Tool to give every editor IDE like capabilities for Nim
Usage:
  nimsuggest [options] [mode] [mode_options] "path/to/projectfile.nim"

Options:
  --nimPath:"path"      Set the path to the Nim compiler.
  --v2                  Use protocol version 2       
  --debug               Enable debug output.
  --help                Print help output for the specified mode.
  --version             Print nimsuggest version to stdout, then quit.

Modes:
  tcp            Use text-based input from a tcp socket.
                 This is the default mode.
  stdin          Use text-based input from stdin (interactive use)
  epc            Use

In addition, all command line options of Nim that do not affect code generation
are supported. To pass a Nim compiler command-line argument, prefix it with
"nim." when passing global options, for example:
  nimsuggest --nim.define:release tcp projectfile.nim
"""

type
  nnstring = string not nil

  ModeData* = ref object of RootObj
    mode*: nnstring
    projectPath*: nnstring
    protocolVersion: int

  ModeInitializer* = proc (): ModeData

  SwitchSequence* = seq[
    tuple[
      kind: CmdLineKind,
      key, value: nnstring
    ]
  ] not nil

  CmdLineData* = object
    mode: nnstring
    nimsuggestSwitches: SwitchSequence
    modeSwitches: SwitchSequence
    compilerSwitches: SwitchSequence
    projectPath: nnstring


# ModeData Method Stubs
method processSwitches(data: ModeData, switches: SwitchSequence) {.base.} =
  raise newException(ValueError, "Mode doesn't implement processSwitches")

method echoOptions(data: ModeData) {.base.} =
  raise newException(ValueError, "Mode doesn't implement echoOptions")

method mainCommand(data: ModeData) {.base.} =
  raise newException(ValueError, "Mode doesn't implement mainCommand")


# Import and add nimsuggest modes
let modes = newTable[string, ModeInitializer]()

import modes/tcpMode, modes/stdinMode, modes/epcMode
tcpMode.addModes(modes)
stdinMode.addModes(modes)
epcmode.addModes(modes)


# Command line logic
proc badUsage(msg: string = nil) =
  if not isNil(msg):
    echo(msg)
  quit()

template ifNotNilElse(a, b, c: untyped): untyped =
  let value = b
  if value == nil:
    a = c
  else:
    a = value


proc gatherCmdLineData(): CmdLineData =
  ## Gather the command line parameters into an CmdLineData object.
  ## This works in two parts: we first get the global nimsuggest switches and
  ## mode, then get the mode switches and project file.
  var parser = initOptParser()
  result = CmdLineData(
      mode: "",
      nimsuggestSwitches: @[],
      modeSwitches: @[],
      compilerSwitches: @[],
      projectPath: ""
    )

  # Get the nimsuggest switches and mode
  while true:
    parser.next()
    case parser.kind
    of cmdLongOption, cmdShortOption:
      # We filter global switches here to allow the user to pass
      # switches to the compiler.
      if parser.key.startsWith("nim."):
        result.compilerSwitches.add(
          (parser.kind, nnstring(parser.key[4..^1]), nnstring(parser.val))
        )
      else:
        result.nimsuggestSwitches.add(
          (parser.kind, nnstring(parser.key), nnstring(parser.val))
        )
    of cmdArgument:
      ifNotNilElse(result.mode, parser.key, "")
      break
    of cmdEnd:
      break

  # Process the remaining mode switches and project file.
  while true:
    parser.next()
    case parser.kind:
    of cmdLongOption, cmdShortOption:
      result.modeSwitches.add(
        (parser.kind, nnstring(parser.key), nnstring(parser.val))
      )
    of cmdArgument:
      # Grab the project file and exit
      ifNotNilElse(result.projectPath, parser.key, "")
      break
    of cmdEnd:
      break

  # Ensure that there are no remaining arguments
  parser.next()
  if parser.kind != cmdEnd:
    badUsage("Error: Extra switches after project file.")


proc setupCompiler(projectPath: string) =
    condsyms.initDefines()
    defineSymbol "nimsuggest"

    gProjectName = unixToNativePath(projectPath)
    if gProjectName != "":
      try:
        gProjectFull = canonicalizePath(gProjectName)
      except OSError:
        gProjectFull = gProjectName
        
      var p = splitFile(gProjectFull)
      gProjectPath = p.dir
    else:
      gProjectPath = getCurrentDir()

    # Find Nim's prefix dir.
    let binaryPath = findExe("nim")
    if binaryPath == "":
      raise newException(IOError,
          "Cannot find Nim standard library: Nim compiler not in PATH")
    gPrefixDir = binaryPath.splitPath().head.parentDir()

    # Load the configuration files
    loadConfigs(DefaultConfig) # load all config files

    extccomp.initVars()
    registerPass verbosePass
    registerPass semPass

    gCmd = cmdIdeTools
    gGlobalOptions.incl(optCaasEnabled)
    isServing = true
    msgs.gErrorMax = high(int)

    wantMainModule()
    appendStr(searchPaths, options.libpath)
    if gProjectFull.len != 0:
      # current path is always looked first for modules
      prependStr(searchPaths, gProjectPath)


proc main =
  if paramCount() == 0:
    echo(helpMsg)
    quit()

  # Gather and process command line data
  var cmdLineData = gatherCmdLineData()
  if not modes.hasKey(cmdLineData.mode.normalize()):
    badUsage("Error: Unknown mode '" & cmdLineData.mode & "'")

  # Initialize the mode and process global switches.
  let modeInitializer = modes[cmdLineData.mode.normalize()]
  var data = modeInitializer()
  data.projectPath = cmdLineData.projectPath

  # Process the nimsuggest switches
  for switch in cmdLineData.nimsuggestSwitches:
    case switch.kind
    of cmdLongOption:
      case switch.key.normalize
      of "help", "h":
        echo(helpMsg)
        data.echoOptions()
        quit()
      of "v2":
        suggestVersion = 2
      of "version":
        echo(nimsuggestVersion)
        quit()
      else:
        quit("Invalid switch '$#:$#'" % [switch.key, switch.value])
    else:
      quit("Invalid switch '$#:$#'" % [switch.key, switch.value])

  # Check for project path here. Checking any earlier leads to --help not
  # working without a project path.
  if cmdLineData.projectPath == "":
    badUsage("Error: Project path not supplied")

  # Process the mode switches
  data.processSwitches(cmdLineData.modeSwitches)

  # Process the compiler switches
  for switch in cmdLineData.compilerSwitches:
    commands.processSwitch(switch.key, switch.value, passCmd1, gCmdLineInfo)

  # Initialize Environment
  setupCompiler(cmdLineData.projectPath)

  # Process the command line again, as some parts may have been overridden by
  # configuration files.
  for switch in cmdLineData.compilerSwitches:
    commands.processSwitch(switch.key, switch.value, passCmd2, gCmdLineInfo)

  var oldHook = msgs.writelnHook
  msgs.writelnHook = (proc (msg: string) = discard)
  compileProject()
  msgs.writelnHook = oldHook

  # echo("gCmd: ", gCmd)
  # echo("gGlobalOptions: ", gGlobalOptions)
  # echo("gProjectFull: ", gProjectFull)
  # echo("gProjectPath: ", gProjectPath)
  # echo("gVerbosity: ", gVerbosity)
  # echo("gProjectName: ", gProjectName)
  # echo("gIdeCmd: ", gIdeCmd)
  # echo("gProjectMainIdx: ", gProjectMainIdx)
  # echo("gErrorCounter: ", gErrorCounter)
  # echo("gPrefixDir: ", gPrefixDir)
  # echo("gTrackPos: ", gTrackPos)

  data.mainCommand()

suggestVersion = 1
when isMainModule:
  main()
