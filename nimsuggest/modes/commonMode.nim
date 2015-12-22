import strutils, os, parseopt, parseutils, sequtils, net, rdstdin, ../sexp
# Do NOT import suggest. It will lead to wierd bugs with
# suggestionResultHook, because suggest.nim is included by sigmatch.
# So we import that one instead.
import ../nimsuggest
import compiler/options, compiler/commands, compiler/modules, compiler/sem,
  compiler/passes, compiler/passaux, compiler/msgs, compiler/nimconf,
  compiler/extccomp, compiler/condsyms, compiler/lists,
  compiler/sigmatch, compiler/ast

when defined(windows):
  import winlean
else:
  import posix

const
  seps = {':', ';', ' ', '\t'}
  

proc parseQuoted*(cmd: string; outp: var string; start: int): int =
  var i = start
  i += skipWhitespace(cmd, i)
  if cmd[i] == '"':
    i += parseUntil(cmd, outp, '"', i+1)+2
  else:
    i += parseUntil(cmd, outp, seps, i)
  result = i

proc findNode(n: PNode): PSym =
  #echo "checking node ", n.info
  if n.kind == nkSym:
    if isTracked(n.info, n.sym.name.s.len): return n.sym
  else:
    for i in 0 ..< safeLen(n):
      let res = n.sons[i].findNode
      if res != nil: return res

proc symFromInfo(gTrackPos: TLineInfo): PSym =
  let m = getModule(gTrackPos.fileIndex)
  #echo m.isNil, " I knew it ", gTrackPos.fileIndex
  if m != nil and m.ast != nil:
    result = m.ast.findNode


proc execute*(cmd: IdeCmd, file, dirtyfile: string, line, col: int) =
  gIdeCmd = cmd
  if cmd == ideUse and suggestVersion != 2:
    modules.resetAllModules()
  var isKnownFile = true
  let dirtyIdx = file.fileInfoIdx(isKnownFile)

  if dirtyfile.len != 0: msgs.setDirtyFile(dirtyIdx, dirtyfile)
  else: msgs.setDirtyFile(dirtyIdx, nil)

  gTrackPos = newLineInfo(dirtyIdx, line, col)
  gErrorCounter = 0
  if suggestVersion < 2:
    usageSym = nil
  if not isKnownFile:
    compileProject()
  if suggestVersion == 2 and gIdeCmd in {ideDef, ideUse, ideDus} and
      dirtyfile.len == 0:
    discard "no need to recompile anything"
  else:
    resetModule dirtyIdx
    if dirtyIdx != gProjectMainIdx:
      resetModule gProjectMainIdx
    compileProject(dirtyIdx)
  if gIdeCmd in {ideUse, ideDus}:
    let u = if suggestVersion >= 2: symFromInfo(gTrackPos) else: usageSym
    if u != nil:
      listUsages(u)
    else:
      localError(gTrackPos, "found no symbol at this position " & $gTrackPos)

proc parseCmdLine*(cmd: string) =
  template toggle(sw) =
    if sw in gGlobalOptions:
      excl(gGlobalOptions, sw)
    else:
      incl(gGlobalOptions, sw)
    return

  template err() =
    echo "Invalid Command"
    return

  var opc = ""
  var i = parseIdent(cmd, opc, 0)
  case opc.normalize
  of "sug": gIdeCmd = ideSug
  of "con": gIdeCmd = ideCon
  of "def": gIdeCmd = ideDef
  of "use": gIdeCmd = ideUse
  of "dus": gIdeCmd = ideDus
  of "chk":
    gIdeCmd = ideChk
    incl(gGlobalOptions, optIdeDebug)
  of "highlight": gIdeCmd = ideHighlight
  of "outline": gIdeCmd = ideOutline
  of "quit": quit()
  of "debug": toggle optIdeDebug
  of "terse": toggle optIdeTerse
  else: err()
  var dirtyfile = ""
  var orig = ""
  i = parseQuoted(cmd, orig, i)
  if cmd[i] == ';':
    i = parseQuoted(cmd, dirtyfile, i+1)
  i += skipWhile(cmd, seps, i)
  var line = -1
  var col = 0
  i += parseInt(cmd, line, i)
  i += skipWhile(cmd, seps, i)
  i += parseInt(cmd, col, i)
  execute(gIdeCmd, orig, dirtyfile, line, col-1)