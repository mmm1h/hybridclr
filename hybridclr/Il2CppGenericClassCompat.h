// Copyright (c) 2026 mmm1h. Licensed under the MIT license in the repository root.
#pragma once

#include "il2cpp-runtime-metadata.h"

#ifndef HYBRIDCLR_UNITY_VERSION
#error "The Unity version must be generated before including this header"
#endif

namespace hybridclr
{
inline const Il2CppGenericInst* GetGenericClassInstance(const Il2CppGenericClass* genericClass)
{
#if HYBRIDCLR_UNITY_VERSION >= 70000000
    return genericClass->class_inst;
#else
    return genericClass->context.class_inst;
#endif
}

// Unity 7 stores only class_inst on a generic class. Return a value so callers
// can give InflateIfNeeded a context whose lifetime covers the entire call.
inline Il2CppGenericContext GetGenericClassContext(const Il2CppGenericClass* genericClass)
{
#if HYBRIDCLR_UNITY_VERSION >= 70000000
    return {genericClass->class_inst, nullptr};
#else
    return genericClass->context;
#endif
}
} // namespace hybridclr
