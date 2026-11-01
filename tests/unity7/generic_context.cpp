// Copyright (c) 2026 mmm1h. Licensed under the MIT license in the repository root.
#include "hybridclr/Il2CppGenericClassCompat.h"

int main()
{
    const Il2CppType* arguments[] = {nullptr, nullptr};
    Il2CppGenericInst instance = {2, arguments};
    Il2CppGenericClass genericClass = {};
#if HYBRIDCLR_UNITY_VERSION >= 70000000
    genericClass.class_inst = &instance;
#else
    genericClass.context = {&instance, nullptr};
#endif
    if (hybridclr::GetGenericClassInstance(&genericClass) != &instance)
        return 1;
    Il2CppGenericContext context = hybridclr::GetGenericClassContext(&genericClass);
    if (context.class_inst != &instance || context.method_inst != nullptr)
        return 2;
    if (context.class_inst->type_argc != 2 || context.class_inst->type_argv != arguments)
        return 3;
    context.class_inst = nullptr;
    if (hybridclr::GetGenericClassInstance(&genericClass) != &instance)
        return 4;
    return 0;
}
