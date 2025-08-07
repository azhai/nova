export function $main() {
@START
  %a =l alloc4 1
  %.t2 =w copy 0
  storeb %.t2, %a
  %b =l alloc4 1
  %.t3 =w copy 0
  storeb %.t3, %b
  %c =l alloc4 1
  %.t4 =w copy 0
  storeh %.t4, %c
  %d =l alloc4 1
  %.t5 =w copy 0
  storeh %.t5, %d
  %.t6 =w loadsb %a
  call $printf(l $L1, w %.t6)
  %.t7 =w copy 126
  storeb %.t7, %a
@L2
  %.t8 =w loadsb %a
  %.t9 =w copy -126
  %.t10 =w cnew %.t8, %.t9
  jnz %.t10, @L4, @L3
@L4
  %.t11 =w loadsb %a
  call $printf(l $L1, w %.t11)
  %.t12 =w loadsb %a
  %.t13 =w copy 1
  %.t12 =w add %.t12, %.t13
  storeb %.t12, %a
  jmp @L2
@L3
  %.t14 =w copy 254
  storeb %.t14, %b
@L5
  %.t15 =w loadub %b
  %.t16 =w copy 2
  %.t17 =w cnew %.t15, %.t16
  jnz %.t17, @L7, @L6
@L7
  %.t18 =w loadub %b
  call $printf(l $L1, w %.t18)
  %.t19 =w loadub %b
  %.t20 =w copy 1
  %.t19 =w add %.t19, %.t20
  storeb %.t19, %b
  jmp @L5
@L6
  %.t21 =w copy 32766
  storeh %.t21, %c
@L8
  %.t22 =w loadsh %c
  %.t23 =w copy -32766
  %.t24 =w cnew %.t22, %.t23
  jnz %.t24, @L10, @L9
@L10
  %.t25 =w loadsh %c
  call $printf(l $L1, w %.t25)
  %.t26 =w loadsh %c
  %.t27 =w copy 1
  %.t26 =w add %.t26, %.t27
  storeh %.t26, %c
  jmp @L8
@L9
  %.t28 =w copy 65532
  storeh %.t28, %d
@L11
  %.t29 =w loaduh %d
  %.t30 =w copy 2
  %.t31 =w cnew %.t29, %.t30
  jnz %.t31, @L13, @L12
@L13
  %.t32 =w loaduh %d
  call $printf(l $L1, w %.t32)
  %.t33 =w loaduh %d
  %.t34 =w copy 1
  %.t33 =w add %.t33, %.t34
  storeh %.t33, %d
  jmp @L11
@L12
@END
  ret
}
data $L1 = { b "%d\n", b 0 }
