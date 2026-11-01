// Copyright (c) 2026 mmm1h. Licensed under the MIT license in the repository root.
#include <windows.h>
#include <atomic>

using DllMainCallback = BOOL(WINAPI*)(HINSTANCE, DWORD, LPVOID);
static std::atomic<DllMainCallback> s_callback{nullptr};

// Unity 7's standalone runtime uses this small DLL to receive thread-detach
// notifications even when libil2cpp itself is linked into the executable.
__declspec(dllexport) void Libil2cppLackeySetDllMain(DllMainCallback callback)
{
    s_callback.store(callback, std::memory_order_release);
}

extern "C" BOOL WINAPI DllMain(HINSTANCE module, DWORD reason, LPVOID reserved)
{
    DllMainCallback callback = s_callback.load(std::memory_order_acquire);
    return callback ? callback(module, reason, reserved) : TRUE;
}
