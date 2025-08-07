export function $main() {
@START
  %a =l alloc4 1
  %.t2 =w copy 1
  storeb %.t2, %a
  %b =l alloc4 1
  %.t3 =w loadsb %a
  %.t3 =w ceqw %.t3, 0
  storeb %.t3, %b
  %.t4 =w loadsb %a
  call $printf(l $L1, w %.t4)
  %.t5 =w loadsb %b
  call $printf(l $L1, w %.t5)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
