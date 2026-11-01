// Copyright (c) 2026 mmm1h. Licensed under the MIT license in the repository root.
#include "hybridclr/Il2CppFloatingPointCompat.h"
#include <cstdio>
#include <cstring>

template<typename T>
void Emit(const char* kind, unsigned long long bits, T value)
{
    std::printf("%s,%llu,%d,%u,%d,%u,%d,%u,%lld,%llu\n", kind, bits,
        (int)il2cpp_codegen_cast_double_to_int<int8_t>(value),
        (unsigned)il2cpp_codegen_cast_floating_point<uint8_t, int32_t>(value),
        (int)il2cpp_codegen_cast_double_to_int<int16_t>(value),
        (unsigned)il2cpp_codegen_cast_floating_point<uint16_t, int32_t>(value),
        il2cpp_codegen_cast_double_to_int<int32_t>(value),
        (unsigned)il2cpp_codegen_cast_floating_point<uint32_t, int32_t>(value),
        (long long)il2cpp_codegen_cast_double_to_int<int64_t>(value),
        (unsigned long long)il2cpp_codegen_cast_floating_point<uint64_t, int64_t>(value));
}

int main()
{
    const uint32_t f4[] = {0, 0x80000000, 0x3fc00000, 0xc0200000, 0x7fc00000, 0x7f800000, 0xff800000,
        0x7f7fffff, 0xff7fffff, 0x4effffff, 0x4f000000, 0xcf000000, 0x4f7fffff, 0x4f800000, 0x5f800000};
    for (uint32_t bits : f4)
    {
        float value;
        std::memcpy(&value, &bits, sizeof(value));
        Emit("f4", bits, value);
    }
    const uint64_t f8[] = {0, 0x8000000000000000ULL, 0x3ff8000000000000ULL, 0xc004000000000000ULL,
        0x7ff8000000000000ULL, 0x7ff0000000000000ULL, 0xfff0000000000000ULL, 0x7fefffffffffffffULL,
        0xffefffffffffffffULL, 0x41dfffffffc00000ULL, 0x41e0000000000000ULL, 0xc1e0000000000000ULL,
        0x41efffffffe00000ULL, 0x41f0000000000000ULL, 0x43e0000000000000ULL, 0x43f0000000000000ULL};
    for (uint64_t bits : f8)
    {
        double value;
        std::memcpy(&value, &bits, sizeof(value));
        Emit("f8", bits, value);
    }
    return 0;
}
