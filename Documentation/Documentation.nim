# Imports
import os, osproc, sequtils
import strutils, json

const mod_path = "modules"

proc dump*: string {.noinit.} =
    ## Generate a list of paths
    osproc.execCmdEx("nim dump").output


iterator documents*(path: string, ext = "*.nim"): string =
    ## Find all `ext` files at specified path
    for file in walkFiles(path / ext):
        yield file


proc make_documentation*(path: string) =

    if path.splitFile.ext != ".nim":
        return

    let outpath = mod_path / os.extractFilename(path).changeFileExt(".json")

    echo path
    discard osproc.execCmdEx(
        "nim jsondoc -o:\"" & outpath &
        "\" \"" & path & "\""
    )


# Ensure `mod_path` directory exists
if not os.existsDir(mod_path):
    os.createDir(mod_path)


# Generate documentation for all documents at search paths
for line in dump().splitLines:
    # Skip this line if the path isn't real
    if not existsDir(line): continue

    # Find all .py documents in path
    for document in line.documents:
        make_documentation(document)


# Create index of all the modules
var module_index = newJArray()
var proc_index   = newJArray()

let allowed_types = ["skProc","skMethod",
                      "skIterator", "skMacro",
                      "skTemplate", "skConverter" ]

for module in documents(mod_path, ext = "*.json"):
    let name       = module.splitFile.name
    let moduleData = json.parseFile(module)

    #Determine top-level module comment
    var description: JsonNode = nil
    for obj in moduleData.items:
        var comment = obj["comment"]
        if comment != nil:
            description = comment
        break

    var indexItem = %{ "module": %name }

    if description != nil:
        indexItem["description"] = description

    module_index.add(indexItem)

    #Write all proc/template/macro/iterator/method/converters
    for obj in moduleData.items:
        let typ = obj["type"]
        if typ != nil and typ.str in allowed_types:
            var row = %{
                "module": %name,
                "name": obj["name"],
                "code": obj["code"]
            }

            let desc = obj["description"]
            if desc != nil and desc.kind == JString:
                row["desc"] = desc

            proc_index.add(row)


writeFile(mod_path / "module_index.json", module_index.pretty)
writeFile(mod_path / "proc_index.json", $proc_index)