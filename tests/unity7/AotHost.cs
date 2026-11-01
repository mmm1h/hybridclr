// Copyright (c) 2026 mmm1h. Licensed under the MIT license in the repository root.
using System;
using System.IO;
using System.Reflection;
using System.Runtime.Loader;

internal static class AotHost
{
    private static void Check(bool value, string name)
    {
        if (!value) throw new InvalidOperationException("Failed: " + name);
        Console.WriteLine("PASS " + name);
    }

    private static object Invoke(Type type, string name, object target, params object[] arguments)
    {
        return type.GetMethod(name).Invoke(target, arguments);
    }

    public static int Main(string[] args)
    {
        try
        {
            Assembly assembly = Assembly.Load(File.ReadAllBytes(args[0]));
            Type type = assembly.GetType("Unity7HotUpdateFixture.Calculator", true);
            object instance = Activator.CreateInstance(type);
            Check((int)Invoke(type, "PayloadVersion", null) == (args.Length > 1 ? int.Parse(args[1]) : 1), "payload-version");
            Check((int)Invoke(type, "Sum", instance, 17, 25) == 42, "reflection-instance-call");
            Check((int)Invoke(type, "InterfaceDispatch", null, 8, 13) == 21, "inherited-interface-dispatch");
            Check((int)Invoke(type, "ArrayData", null) == 12, "field-rva-array-initialization");
            MethodInfo generic = type.GetMethod("Echo").MakeGenericMethod(typeof(int));
            Check((int)generic.Invoke(null, new object[] { 123 }) == 123, "closed-generic-method");
            var adder = (Func<int, int>)Invoke(type, "MakeAdder", null, 9);
            GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect();
            Check(adder(6) == 15, "delegate-and-gc");
            Check((bool)Invoke(type, "AtomicOperations", null), "atomic-integer-and-object-operations");
            Check((bool)Invoke(type, "RejectLegacyDelegateAsync", null), "legacy-delegate-async-rejected");
            Check((string)Invoke(type, "ExceptionMessage", null) == "hot-exception", "managed-exception");
            try { Invoke(type, "ThrowFromHotCode", null); throw new Exception("Expected hot exception"); }
            catch (TargetInvocationException ex)
            {
                Check(ex.InnerException is InvalidOperationException && ex.InnerException.Message == "hot-propagated"
                    && ex.InnerException.StackTrace.Contains("ThrowFromHotCode"), "hot-exception-stack-trace");
            }
            Check((bool)type.GetField("ContextReady").GetValue(null), "load-context-before-module-initializer");
            Check(AssemblyLoadContext.GetLoadContext(assembly) != null, "assembly-load-context-identity");
            object[] attributes = type.GetCustomAttributes(false);
            Check(attributes.Length == 1 && (int)attributes[0].GetType().GetProperty("Number").GetValue(attributes[0]) == 23, "custom-attribute");
            Check(type.GetProperty("MarkedProperty").GetCustomAttributes(false).Length == 1, "property-attribute");
            Check(type.GetMethod("MarkedReturn").ReturnParameter.GetCustomAttributes(false).Length == 1, "return-parameter-attribute");
            Check(assembly.ManifestModule.MetadataToken == 1, "manifest-module-token");
            Check(Array.Exists(AppDomain.CurrentDomain.GetAssemblies(), candidate => candidate == assembly), "loaded-assembly-enumeration");
            try { new AssemblyLoadContext("collectible", isCollectible: true); throw new Exception("Expected unsupported collectible context"); }
            catch (PlatformNotSupportedException) { Console.WriteLine("PASS collectible-context-rejected"); }
            Console.WriteLine("HYBRIDCLR_UNITY7_HOT_UPDATE_OK");
            return 0;
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error.ToString());
            return 1;
        }
    }
}
