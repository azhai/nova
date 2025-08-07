export function $main() {
@START
  %fred =l alloc8 1
  %.t2 =l copy 34
  storel %.t2, %fred
  %.t3 =l copy 100
  storel %.t3, %fred
  %.t4 =l loadl %fred
  %.t5 =l copy 2
  %.t4 =l add %.t4, %.t5
  call $printf(l $L1, l %.t4)
  %.t6 =l loadl %fred
  %.t7 =l copy 100
  %.t6 =l add %.t6, %.t7
  storel %.t6, %fred
  %.t8 =l loadl %fred
  call $printf(l $L1, l %.t8)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
