include "emu8086.inc"

.model small
.stack 100h

.data
    X      dw 10
    Y      dw 4
    Z      dw 3
    Result dw ?

.code
main proc
    mov ax, @data
    mov ds, ax

    printn "=== Assignment Program Started ==="

    jmp skip_dummy
    mov ax, 9999        ; dummy block (skipped)
    mov bx, 8888

skip_dummy:
    printn "Step 1: Calling procedure to calculate (X - Y) * Z"

    push X
    push Y
    push Z
    call calculate_core

    printn "Step 2: Processing division and addition in Main..."

    mov cx, 2
    cwd
    idiv cx             ; AX = AX / 2
    add ax, 5           ; AX = AX + 5
    mov Result, ax

    printn "Step 3: Calculation Completed Successfully!"
    printn "Result is stored in variable 'Result'."

    mov ah, 4Ch
    int 21h
main endp

calculate_core proc
    pop dx              ; save return address
    pop cx              ; Z
    pop bx              ; Y
    pop ax              ; X
    push dx             ; restore return address

    sub ax, bx          ; X - Y
    imul cx             ; (X - Y) * Z
    ret
calculate_core endp

end main
