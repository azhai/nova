export function $main() {
@START
  %fred =l alloc4 1
  %.t2 =w copy 23
  storeb %.t2, %fred
  %jim =l alloc4 1
  %.t3 =w copy -7
  storeb %.t3, %jim
  %.t4 =w loadsb %jim
  %.t5 =w loadsb %fred
  %.t4 =w add %.t4, %.t5
  storeb %.t4, %jim
  %.t6 =w loadsb %jim
  call $printf(l $L1, w %.t6)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
