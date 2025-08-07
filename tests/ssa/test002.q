export function $main() {
@START
  %fred =l alloc4 1
  %.t2 =w copy 45
  storew %.t2, %fred
  %.t3 =w copy 32
  %.t4 =w copy 2
  %.t5 =w copy 3
  %.t4 =w mul %.t4, %.t5
  %.t3 =w add %.t3, %.t4
  %.t6 =w copy 5
  %.t3 =w sub %.t3, %.t6
  call $printf(l $L1, w %.t3)
  %.t7 =w copy 1001
  call $printf(l $L1, w %.t7)
  %.t8 =w copy 23
  %.t8 =w sub 0, %.t8
  %.t9 =w copy 2
  %.t8 =w add %.t8, %.t9
  call $printf(l $L1, w %.t8)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
