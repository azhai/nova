export function $main() {
@START
  %x =l alloc4 1
  %.t2 =w copy 0
  storew %.t2, %x
@L1
  %.t3 =w loadsw %x
  %.t4 =w copy 30
  %.t5 =w csltw %.t3, %.t4
  jnz %.t5, @L3, @L2
@L3
  %.t6 =w loadsw %x
  call $printf(l $L4, w %.t6)
  %.t7 =w loadsw %x
  %.t8 =w copy 1
  %.t7 =w add %.t7, %.t8
  storew %.t7, %x
  jmp @L1
@L2
@END
  ret
}
data $L4 = { b "%d\n", b 0 }
