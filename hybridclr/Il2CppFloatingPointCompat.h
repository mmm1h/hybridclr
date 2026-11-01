// Copyright (c) 2026 mmm1h. Licensed under the MIT license in the repository root.
#pragma once

#include "codegen/il2cpp-codegen.h"

#if HYBRIDCLR_UNITY_VERSION >= 70000000
// Keep the generated interpreter's conversion calls while using the same
// conversion policy as Unity 7's generated AOT code, including NaN/overflow.
template<typename T>
inline T il2cpp_codegen_cast_double_to_int(double value)
{
    return ConvFloatingPoint<T, double>::Conv(value);
}

template<typename TInput, typename TOutput, typename TFloat>
inline TOutput il2cpp_codegen_cast_floating_point(TFloat value)
{
    return (TOutput)ConvFloatingPoint<TInput, TFloat>::Conv(value);
}
#endif
