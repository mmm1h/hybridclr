// Copyright (c) 2026 mmm1h. Licensed under the MIT license in the repository root.
using System;
using System.Runtime.CompilerServices;
using System.Runtime.Loader;
using System.Threading;

namespace Unity7HotUpdateFixture
{
    public interface ISum { int Sum(int a, int b); }
    public interface ICalculator : ISum { }

    [AttributeUsage(AttributeTargets.Class | AttributeTargets.Method | AttributeTargets.ReturnValue)]
    public sealed class MarkerAttribute : Attribute
    {
        public string Name { get; }
        public MarkerAttribute(string name) { Name = name; }
    }

    [Marker("loaded-from-bytes")]
    public sealed class Calculator : ICalculator
    {
        private static readonly int[] Values = { 3, 4, 5 };
        public static bool ContextReady;

        [ModuleInitializer]
        public static void Initialize()
        {
            ContextReady = AssemblyLoadContext.GetLoadContext(typeof(Calculator).Assembly) != null;
        }

        public int Sum(int a, int b) { return a + b; }
        public static int InterfaceDispatch(int a, int b) { ICalculator value = new Calculator(); return value.Sum(a, b); }
        public static int ArrayData() { return Values[0] + Values[1] + Values[2]; }
        public static T Echo<T>(T value) { return value; }
        public static Func<int, int> MakeAdder(int delta) { return value => value + delta; }

        public static int PayloadVersion()
        {
#if PAYLOAD_V2
            return 2;
#else
            return 1;
#endif
        }

        public static bool AtomicOperations()
        {
            int number = 0;
            long wide = 0;
            if (Interlocked.Increment(ref number) != 1 || Interlocked.Add(ref wide, 7) != 7) return false;
            if (Interlocked.CompareExchange(ref number, 4, 1) != 1 || number != 4) return false;
            if (Interlocked.Exchange(ref wide, 11) != 7 || wide != 11) return false;
            object first = new object(), second = new object(), target = first;
            if (Interlocked.CompareExchange(ref target, second, first) != first || target != second) return false;
            if (Interlocked.Exchange(ref target, first) != second || target != first) return false;
            GC.Collect();
            return ReferenceEquals(target, first);
        }

        public delegate int LegacyAsync(int value);
        public static bool RejectLegacyDelegateAsync()
        {
            LegacyAsync callback = value => value + 1;
            try { callback.BeginInvoke(1, null, null); return false; }
            catch (PlatformNotSupportedException) { return true; }
        }

        public static void ThrowFromHotCode() { throw new InvalidOperationException("hot-propagated"); }

        public static string ExceptionMessage()
        {
            try { throw new InvalidOperationException("hot-exception"); }
            catch (InvalidOperationException ex) { return ex.Message; }
        }

        [return: Marker("return-token")]
        public static int MarkedReturn() { return 37; }
    }
}
