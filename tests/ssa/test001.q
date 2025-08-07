export function $main() {
@START
  %.t2 =w copy 32
  %.t3 =w copy 2
  %.t4 =w copy 3
  %.t3 =w mul %.t3, %.t4
  %.t2 =w add %.t2, %.t3
  %.t5 =w copy 5
  %.t2 =w sub %.t2, %.t5
  call $printf(l $L1, w %.t2)
  %.t6 =w copy 10
  %.t7 =w copy 5
  %.t6 =w add %.t6, %.t7
  call $printf(l $L1, w %.t6)
  %.t8 =w copy 23
  %.t9 =w copy 5
  %.t10 =w copy 6
  %.t9 =w mul %.t9, %.t10
  %.t8 =w sub %.t8, %.t9
  %.t11 =w copy 9
  %.t8 =w add %.t8, %.t11
  call $printf(l $L1, w %.t8)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
