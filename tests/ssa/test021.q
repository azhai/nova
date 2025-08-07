export function $main() {
@START
  %x =l alloc4 1
  %.t2 =w copy 1
  %.t3 =w copy 3
  %.t2 =w add %.t2, %.t3
  storew %.t2, %x
  %.t5 =w loadsw %x
  call $printf(l $L1, w %.t5)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
