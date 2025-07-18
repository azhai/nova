export function $main() {
@START
  %fred =l alloc8 1
  %.t2 =l copy 34
  storel %.t2, %fred
  %.t3 =w copy 2
  %.t4 =w copy 3
  %.t3 =w mul %.t3, %.t4
  %.t5 =w copy 7
  %.t3 =w add %.t3, %.t5
  %.t6 =l extsw %.t3
  %.t7 =l loadl %fred
  %.t6 =l add %.t6, %.t7
  call $printf(l $L1, l %.t6)
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
