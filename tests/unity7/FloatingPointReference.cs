// Copyright (c) 2026 mmm1h. Licensed under the MIT license in the repository root.
using System;
using System.Globalization;

internal static class FloatingPointReference
{
    private static void Emit(uint bits)
    {
        float value = BitConverter.Int32BitsToSingle(unchecked((int)bits));
        unchecked
        {
            Console.WriteLine(string.Join(",", new object[] { "f4", bits, (sbyte)value, (byte)value,
                (short)value, (ushort)value, (int)value, (uint)value, (long)value, (ulong)value }));
        }
    }

    private static void Emit(ulong bits)
    {
        double value = BitConverter.Int64BitsToDouble(unchecked((long)bits));
        unchecked
        {
            Console.WriteLine(string.Join(",", new object[] { "f8", bits, (sbyte)value, (byte)value,
                (short)value, (ushort)value, (int)value, (uint)value, (long)value, (ulong)value }));
        }
    }

    public static void Main()
    {
        CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
        foreach (uint bits in new uint[] { 0, 0x80000000, 0x3fc00000, 0xc0200000, 0x7fc00000, 0x7f800000, 0xff800000,
            0x7f7fffff, 0xff7fffff, 0x4effffff, 0x4f000000, 0xcf000000, 0x4f7fffff, 0x4f800000, 0x5f800000 }) Emit(bits);
        foreach (ulong bits in new ulong[] { 0, 0x8000000000000000, 0x3ff8000000000000, 0xc004000000000000,
            0x7ff8000000000000, 0x7ff0000000000000, 0xfff0000000000000, 0x7fefffffffffffff,
            0xffefffffffffffff, 0x41dfffffffc00000, 0x41e0000000000000, 0xc1e0000000000000,
            0x41efffffffe00000, 0x41f0000000000000, 0x43e0000000000000, 0x43f0000000000000 }) Emit(bits);
    }
}
