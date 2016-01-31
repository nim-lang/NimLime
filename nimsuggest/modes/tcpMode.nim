import tables, net, parseopt2, strutils
import ../nimsuggest, commonMode
import compiler/msgs
from os import nil

const tcpModeHelpMsg = """
Nimsuggest TCP Mode Switches:
  -p, --port:port_no         Port to use to connect (defaults to 8000).
  --address:"address"        Address to bind/connect to. Defaults to ""
  --persist                  Create a persistant connection that isn't closed
                             after the first completed command. Completed
                             commands are then denoted by a newline.
                             Not compatible with the 'client' switch.
  --client                   Act as a client. In client mode the nimsuggest
                             tool will attempt to connect to the address and
                             port specified by the 'address' and 'port'
                             switches, instead of binding to them as a server.
"""


type TcpModeData = ref object of ModeData
  port: Port
  address: string not nil
  client: bool
  persist: bool


proc initializeData*(): ModeData =
  var res = new(TcpModeData)
  res.port = Port(0)
  res.address = ""
  res.client = false

  result = ModeData(res)

proc addModes*(modes: TableRef[string, ModeInitializer]) =
  modes["tcp"] = initializeData


# ModeData Interface Methods
method processSwitches(data: TcpModeData, switches: SwitchSequence) =
  for switch in switches:
    case switch.kind
    of cmdLongOption, cmdShortOption:
      case switch.key.normalize
      of "p", "port":
        try:
          data.port = Port(parseInt(switch.value))
        except ValueError:
          quit("Invalid port:'" & switch.value & "'")
      of "address":
        data.address = switch.value
      of "client":
        data.client = true
      of "persist":
        if switch.value == "":
          data.persist = true
        else:
          try:
            data.persist = parseBool(switch.value)
          except ValueError:
            quit("Invalid 'persistance' value '" & switch.value & "'")
      else:
        echo("Invalid mode switch '$#'" % [switch.key])
        quit()
    else:
      discard

method echoOptions(data: TcpModeData) =
  echo(tcpModeHelpMsg)
  quit()


proc serveAsServer(data: TcpModeData) =
  var 
    server = newSocket()
    stdoutSocket: Socket
    inp = "".TaintedString
  server.bindAddr(data.port, data.address)
  server.listen()

  template setupStdoutSocket = 
    stdoutSocket = newSocket()
    msgs.writelnHook = proc (line: string) =
      stdoutSocket.send(line & "\c\L")
    accept(server, stdoutSocket)

  setupStdoutSocket()
  while true:
    stdoutSocket.readLine(inp)
    parseCmdLine inp.string
    stdoutSocket.send("\c\L")

    if not data.persist:
      stdoutSocket.close()
      setupStdoutSocket()

proc serveAsClient(data: TcpModeData) =
  var
    input = "".TaintedString
    stdoutSocket: Socket

  while true:
    if stdoutSocket == nil:
      stdoutSocket = newSocket()
      stdoutSocket.connect(data.address, data.port)
      msgs.writelnHook = proc (line: string) =
        stdoutSocket.send(line & "\c\L")

    try:
      stdoutSocket.readLine(input)
      if input == "":
        stdoutSocket = nil
        continue
      parseCmdLine(string(input))
      stdoutSocket.send("\c\l\c\l")
    except OSError:
      quit()

method mainCommand(data: TcpModeData) =
  msgs.writelnHook = proc (msg: string) = discard
  echo("Running Nimsuggest TCP Mode on port $#, address \"$#\"" % [$data.port, data.address])
  echo("Project file: \"$#\"" % [data.projectPath])
  if data.client:
    serveAsClient(data)
  else:
    serveAsServer(data)