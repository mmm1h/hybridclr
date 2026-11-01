// Copyright (c) 2026 mmm1h. Licensed under the MIT license in the repository root.
#include "vm/MetadataDeserialization.h"
#include <cstdint>
#include <vector>

static void Write(std::vector<char>& data, uint32_t value, int width)
{
    for (int i = 0; i < width; ++i) data.push_back((char)(value >> (8 * i)));
}

int main()
{
    for (int width : {1, 2, 4})
    {
        SerializedIndexSizes sizes;
        sizes.typeIndex = sizes.typeDefinitionIndex = sizes.parameterIndex = sizes.genericContainerIndex = width;
        sizes.fieldIndex = sizes.methodIndex = sizes.eventIndex = sizes.propertyIndex = width;
        sizes.nestedTypeIndex = sizes.interfacesIndex = width;

        std::vector<char> method;
        Write(method, 11, 4); Write(method, 12, width);
        Write(method, UINT32_MAX, width); Write(method, UINT32_MAX, width);
        Write(method, 6, 2); Write(method, 0x4000, 2); Write(method, 7, 2); Write(method, 0x12345678, 4);
        const size_t methodStride = method.size();
        const auto copy = method;
        method.insert(method.end(), copy.begin(), copy.end());
        for (size_t offset : {size_t(0), methodStride})
        {
            auto value = DeserializeMethodDefinition(reinterpret_cast<Il2CppMetadataMethodDefinitionHandle>(method.data() + offset), sizes);
            if (value.nameIndex != 11 || value.declaringType != 12 || value.parameterStart != -1 || value.genericContainerIndex != -1)
                return 1;
            if (value.flags != 6 || value.iflags != 0x4000 || value.slot != 7 || value.methodSigOffset != 0x12345678)
                return 2;
            if (value.token != 0 || value.returnType != 0 || value.returnParameterToken != 0 || value.parameterCount != 0)
                return 3;
        }
        if (methodStride != size_t(14 + 3 * width) || sizeof(Il2CppMethodDefinition) <= methodStride)
            return 4;

        std::vector<char> type;
        Write(type, 20, 4); Write(type, 21, 4); Write(type, 22, width);
        Write(type, UINT32_MAX, width); Write(type, 23, width); Write(type, UINT32_MAX, width);
        Write(type, 0x100001, 4);
        for (uint32_t value : {24, 25, 26, 27, 28, 29}) Write(type, value, width);
        Write(type, 30, 4); Write(type, 31, width);
        for (uint32_t count = 1; count <= 8; ++count) Write(type, count, 2);
        Write(type, 0x10010, 4);
        const auto decoded = DeserializeTypeDefinition(reinterpret_cast<Il2CppMetadataTypeHandle>(type.data()), sizes);
        if (decoded.nameIndex != 20 || decoded.namespaceIndex != 21 || decoded.byvalTypeIndex != 22 || decoded.declaringTypeIndex != -1)
            return 5;
        if (decoded.parentIndex != 23 || decoded.genericContainerIndex != -1 || decoded.flags != 0x100001)
            return 6;
        if (decoded.fieldStart != 24 || decoded.methodStart != 25 || decoded.eventStart != 26 || decoded.propertyStart != 27 ||
            decoded.nestedTypesStart != 28 || decoded.interfacesStart != 29 || decoded.vtableStart != 30 || decoded.interfaceOffsetsStart != 31)
            return 7;
        if (decoded.method_count != 1 || decoded.property_count != 2 || decoded.field_count != 3 || decoded.event_count != 4 ||
            decoded.nested_type_count != 5 || decoded.vtable_count != 6 || decoded.interfaces_count != 7 || decoded.interface_offsets_count != 8)
            return 8;
        if (decoded.bitfield != 0x10010 || decoded.typeHandle != nullptr || decoded.token != 0)
            return 9;

        std::vector<char> parameter;
        Write(parameter, 42, 4);
        const auto param = DeserializeParameterDefinition(parameter.data(), sizes);
        if (param.nameIndex != 42 || param.token != 0 || param.typeIndex != 0)
            return 10;
    }
    return 0;
}
