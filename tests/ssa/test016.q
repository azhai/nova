export function $main() {
@START
  %a =l alloc4 1
  %.t2 =w copy 0
  storew %.t2, %a
  %.t3 =w copy 255
  %.t4 =w copy 3
  %.t3 =w and %.t3, %.t4
  storew %.t3, %a
  %.t6 =w loadsw %a
  call $printf(l $L1, w %.t6)
  %.t7 =w copy 15
  %.t8 =w copy 240
  %.t7 =w or %.t7, %.t8
  storew %.t7, %a
  %.t10 =w loadsw %a
  call $printf(l $L1, w %.t10)
  %.t11 =w copy 255
  %.t12 =w copy 1
  %.t11 =w xor %.t11, %.t12
  storew %.t11, %a
  %.t14 =w loadsw %a
  call $printf(l $L1, w %.t14)
  %.t15 =w copy 0
  %.t15 =w xor %.t15, -1
  storew %.t15, %a
  %.t17 =w loadsw %a
  call $printf(l $L1, w %.t17)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
