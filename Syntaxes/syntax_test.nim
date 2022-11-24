# SYNTAX TEST "Packages/NimLime/Syntaxes/Nim.sublime-syntax"
# <- source.nim comment.line.number-sign punctuation.definition.comment

discard """
#^^^^^^^^^^ comment.block.nim punctuation.definition.comment.begin.nim
"""

#[
    multi-line comment
    #[
        nested comment 
    ]#
]#

proc f =
  ## doc comment
# ^^ comment.line.documentation.nim punctuation.definition.comment.nim
  ##[
# ^^^ comment.block.documentation.nim punctuation.definition.comment.begin.nim
    multi-line doc comment
    ##[
#   ^^^ comment.block.documentation.nim comment.block.documentation.nim punctuation.definition.comment.begin.nim
      can be nested too
    ]##
#   ^^^ comment.block.documentation.nim comment.block.documentation.nim punctuation.definition.comment.end.nim
  ]##
# ^^^ comment.block.documentation.nim punctuation.definition.comment.end.nim

# Literals
##########

 "Valid escape characters forms: \n, \N, \x42, \u4532 or \u{90211234}"
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.string.nim string.quoted.double.nim
#^ punctuation.definition.string.begin.nim
#                                ^^ constant.character.escape.nim
#                                                                    ^ punctuation.definition.string.end.nim
 "unclosed
#^^^^^^^^^ meta.string.nim string.quoted.double.nim
#^ punctuation.definition.string.begin.nim
#         ^ meta.string.nim string.quoted.double.nim invalid.illegal.nim
 r"raw string \Li\teral ""\x23"""
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.string.nim
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ string.quoted.double.nim
# ^ punctuation.definition.string.begin.nim
#                       ^^ constant.character.escape.double-quote.nim
#                             ^^ constant.character.escape.double-quote.nim
#                               ^ punctuation.definition.string.end.nim
 """
#^^^ meta.string.nim string.quoted.double.block.nim punctuation.definition.string.begin.nim
   Multi-line string \t \x21 ""
#^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ meta.string.nim string.quoted.double.block.nim
 """"""
#^^^^^^ meta.string.nim string.quoted.double.block.nim
#   ^^^ punctuation.definition.string.end.nim
 R""""
#^^^^^ meta.string.nim
#^ storage.type.string.nim
# ^^^ string.quoted.double.block.nim punctuation.definition.string.begin.nim
 Identical to normal multi-line string
 """"
#^^^^ meta.string.nim string.quoted.double.block.nim
# ^^^ punctuation.definition.string.end.nim


 'm'
#^^^ constant.character.nim
 '\x12'
#^^^^^^ constant.character.nim
# ^^^^ constant.character.escape.nim
 '\n'
# ^^ constant.character.escape.nim
 '\L'
# ^^ constant.character.escape.nim
 '\'
#^^^ invalid.illegal.nim
 'chars'
#^^^^^^^ invalid.illegal.nim

 1
#^ meta.number.integer.decimal.nim constant.numeric.value.nim
 1.2
#^^^ meta.number.float.decimal.nim constant.numeric.value.nim
# ^ punctuation.separator.decimal.nim
 1.2e2
#^^^^^ meta.number.float.decimal.nim
#^^^ constant.numeric.value.nim
# ^ punctuation.separator.decimal.nim
#   ^^ constant.numeric.value.exponent.nim
 -1.205f64
#^ keyword.operator.nim
# ^^^^^^^^ meta.number.float.decimal.nim
# ^^^^^ constant.numeric.value.nim
#  ^ punctuation.separator.decimal.nim
#      ^^^ constant.numeric.suffix.nim
 1.2E-10'f32
#^^^^^^^^^^^ meta.number.float.decimal.nim
#^^^ constant.numeric.value.nim
# ^ punctuation.separator.decimal.nim
#   ^^^^ constant.numeric.value.exponent.nim
#       ^^^^ constant.numeric.suffix.nim
 0b1'u32
#^^^^^^^ meta.number.float.binary.nim
#^^ constant.numeric.base.nim
#  ^ constant.numeric.value.nim
#   ^^^^ constant.numeric.suffix.nim
 0xf32f32
#^^^^^^^^ meta.number.float.hexadecimal.nim
#^^ constant.numeric.base.nim
#  ^^^ constant.numeric.value.nim
#     ^^^ constant.numeric.suffix.nim
 0o7210'big
#^^^^^^^^^^ meta.number.float.octal.nim
#^^ constant.numeric.base.nim
#  ^^^^ constant.numeric.value.nim
#      ^^^^ constant.numeric.suffix.nim
 0o7210big
#^^^^^^ meta.number.integer.octal.nim
#^^ constant.numeric.base.nim
#  ^^^^ constant.numeric.value.nim
 0.9*a
#^^^ meta.number.float.decimal.nim constant.numeric.value.nim
# ^ punctuation.separator.decimal.nim
#   ^ keyword.operator.nim

const c = false
#^^^^ storage.modifier.nim keyword.declaration.constant.nim
#     ^ entity.name.constant.nim
#       ^ keyword.operator.assignment.nim
#         ^^^^^ constant.language.nim
const (c1*, c2) = (m, not a)
#^^^^ storage.modifier.nim keyword.declaration.constant.nim
#     ^ punctuation.section.parens.begin.nim
#      ^^ entity.name.constant.nim
#        ^ storage.modifier.nim
#         ^ punctuation.separator.nim
#           ^^ entity.name.constant.nim
#             ^ punctuation.section.parens.end.nim
#               ^ keyword.operator.assignment.nim
#                 ^ punctuation.section.parens.begin.nim
#                   ^ punctuation.separator.nim
#                     ^^^ keyword.operator.logical.nim
#                          ^ punctuation.section.parens.end.nim
const
  #^^ storage.modifier.nim keyword.declaration.constant.nim
  pi*: float32 = 3.14
  #^ entity.name.constant.nim
  # ^ storage.modifier.nim
  #  ^ punctuation.separator.annotation.nim
  #    ^^^^^^^ storage.type.primitive.nim
  abc {.pr} = 5
  #^^ entity.name.constant.nim
  #   ^^^^^ meta.annotation.nim
  #   ^^ punctuation.definition.annotation.begin.nim
  #     ^^ entity.other.attribute-name.pragma.nim
  #       ^ punctuation.definition.annotation.end.nim

  abc, d =
  #^^ entity.name.constant.nim
  #  ^ invalid.illegal.nim
  (abc, d) =
  #<- punctuation.section.parens.begin.nim
  #^^^ entity.name.constant.nim
  #   ^ punctuation.separator.nim
  #     ^ entity.name.constant.nim
  #      ^ punctuation.section.parens.end.nim
  (def {.m}, ):
  #<- punctuation.section.parens.begin.nim
  #^^^ entity.name.constant.nim
  #    ^^^^ meta.annotation.nim
  #        ^ punctuation.separator.nim
  #          ^ punctuation.section.parens.end.nim
  #           ^ invalid.illegal.nim

 var name = "m"
#^^^ storage.modifier.nim keyword.declaration.variable.nim
#    ^^^^ entity.name.variable.nim
 var noun, pronoun: string
#^^^ storage.modifier.nim keyword.declaration.variable.nim
#    ^^^^ entity.name.variable.nim
#        ^ punctuation.separator.nim
#          ^^^^^^^ entity.name.variable.nim
#                 ^ punctuation.separator.annotation.nim
#                   ^^^^^^ storage.type.primitive.nim
var
  a = 0
  #<- entity.name.variable.nim
  # ^ keyword.operator.assignment.nim
  b: array[1..10, uint8]
  #<- entity.name.variable.nim
  #^ punctuation.separator.annotation.nim
  #  ^^^^^ storage.type.primitive.nim
  #       ^^^^^^^^^^^^^^ meta.generic.nim
  #       ^ punctuation.section.generic.begin.nim
  #        ^ meta.number.integer.decimal.nim constant.numeric.value.nim
  #         ^^ keyword.operator.nim
  #           ^^ meta.number.integer.decimal.nim constant.numeric.value.nim
  #             ^ punctuation.separator.nim
  #               ^^^^^ storage.type.primitive.nim
  #                    ^ punctuation.section.generic.end.nim
  c {.ma}: int
  #<- entity.name.variable.nim
  # ^^^^^ meta.annotation.nim
  #      ^ punctuation.separator.annotation.nim
  #        ^^^ storage.type.primitive.nim

 while true:
#^^^^^ keyword.control.loop.while.nim
#      ^^^^ constant.language.nim
#          ^ punctuation.section.block.begin.nim
  case state:
# ^^^^ keyword.control.conditional.switch.nim
#           ^ punctuation.section.block.begin.nim
  of asleep:
# ^^ keyword.control.conditional.case.nim
#          ^ punctuation.section.block.begin.nim
    wakeup()
#   ^^^^^^ meta.function-call.nim variable.function.nim
#         ^^ meta.function-call.arguments.nim
#         ^ punctuation.section.arguments.begin.nim
#          ^ punctuation.section.arguments.end.nim
  else awake:
# ^^^^ keyword.control.conditional.else.nim
#           ^ punctuation.section.block.begin.nim
    sleep(`for`=2.days)
#   ^^^^^ meta.function-call.nim variable.function.nim
#        ^^^^^^^^^^^^^^ meta.function-call.arguments.nim
#        ^ punctuation.section.arguments.begin.nim
#         ^^^^^ variable.parameter.nim
#              ^ keyword.operator.assignment.nim
#               ^ meta.number.integer.decimal.nim constant.numeric.value.nim
#                ^ punctuation.accessor.dot.nim
#                     ^ punctuation.section.arguments.end.nim

  for (i, c) in iter:
# ^^^ keyword.control.loop.for.nim
#     ^ punctuation.section.parens.begin.nim
#       ^ punctuation.separator.nim
#          ^ punctuation.section.parens.end.nim
#            ^^ keyword.control.loop.for.in.nim
#                   ^ punctuation.section.block.begin.nim
    for i
#   ^^^ keyword.control.loop.for.nim
      in 1..10:
#     ^^ keyword.control.loop.for.in.nim
#             ^ punctuation.section.block.begin.nim
    let a = d[0]
#   ^^^ storage.modifier.nim keyword.declaration.variable.nim
#       ^ entity.name.variable.nim
#         ^ keyword.operator.assignment.nim
#            ^ punctuation.section.brackets.begin.nim
#              ^ punctuation.section.brackets.end.nim
    echo(c)
#   ^^^^ meta.function-call.nim variable.function.nim support.function.builtin.nim
#       ^^^ meta.function-call.arguments.nim
#       ^ punctuation.section.arguments.begin.nim
#         ^ punctuation.section.arguments.end.nim
 proc m:
#^^^^^^^ meta.function.nim
#^^^^ storage.type.function.nim keyword.declaration.function.nim
#     ^ entity.name.function.nim
#      ^ punctuation.separator.annotation.return.nim

