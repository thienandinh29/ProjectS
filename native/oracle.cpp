// SPDX-License-Identifier: GPL-3.0-or-later
// Offline oracle only: this DLL never observes or sends keyboard input.
#include <cstring>
#include "unikey.h"

extern "C" __declspec(dllexport) void oracle_init(int modern) {
    static bool ready = false;
    if (!ready) { UnikeySetup(); ready = true; }
    UnikeyOptions opt = {};
    CreateDefaultUnikeyOptions(&opt);
    opt.freeMarking = 1;
    opt.modernStyle = modern;
    opt.spellCheckEnabled = 0;
    opt.autoNonVnRestore = 0;
    opt.macroEnabled = 0;
    UnikeySetOptions(&opt);
    UnikeyResetBuf();
}

extern "C" __declspec(dllexport) void oracle_reset() { UnikeyResetBuf(); }

// Returns UTF-8 replacement bytes; backspaces count displayed code points.
extern "C" __declspec(dllexport) int oracle_key(unsigned int ch, int* backs,
                                              unsigned char* out, int cap) {
    UnikeySetCapsState(ch >= 'A' && ch <= 'Z', 0);
    if (ch == 8) UnikeyBackspacePress();
    else UnikeyFilter(ch);
    *backs = UnikeyBackspaces;
    if (UnikeyBufChars > cap) return -1;
    if (UnikeyBufChars > 0) std::memcpy(out, UnikeyBuf, UnikeyBufChars);
    return UnikeyBufChars;
}
