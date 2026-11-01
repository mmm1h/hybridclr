// Copyright (c) 2026 mmm1h. Licensed under the MIT license in the repository root.
#include "hybridclr/Il2CppCompatibleDef.h"

Il2CppException* ProbeTypeLoadException(const char* message)
{
    return hybridclr::GetTypeLoadException(message);
}

std::string ProbeReflectionName(const Il2CppType* type)
{
    return hybridclr::GetKlassFullName2(type);
}

Il2CppGenericContext ProbeGenericContext(const Il2CppGenericClass* genericClass)
{
    return hybridclr::GetGenericClassContext(genericClass);
}
