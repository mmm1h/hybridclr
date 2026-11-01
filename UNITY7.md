# Unity 7 原生移植

本维护分支以官方 `v6000.3.x-9.0.1` 为基线，只针对 Unity `7000.0.0a12`，修订 `8751f7c83ed7`。Unity 7 使用新的 .NET BCL、压缩元数据和运行时 ABI；配套 [il2cpp_plus](https://github.com/mmm1h/il2cpp_plus/tree/codex/unity7-support) 在本机原版源码上应用补丁，不复用 Unity 6 运行库。

移植覆盖压缩签名和 token 重建、解释器元数据分发、泛型上下文、接口分发、动态 GC 根、反射和程序集字节流加载。新 BCL 的浮点转换与 CLR 一致；委托 `BeginInvoke` 和 `EndInvoke` 抛出 `PlatformNotSupportedException`。程序集加载支持非回收上下文，回收上下文明确拒绝；不提供程序集卸载或上下文隔离。

Win64 独立 IL2CPP 测试已通过两版外部热更 DLL，主程序保持相同哈希。覆盖反射调用、继承接口、数组 RVA、泛型、委托与 GC、原子操作、异常堆栈、模块初始化、加载上下文、特性、返回值特性和程序集枚举。浮点转整数结果与 .NET 10 对照一致，元数据解码检查覆盖不同索引宽度。测试使用真实生成的桥接代码，热更 DLL 不参与 AOT 转换。

Windows 和 macOS 编辑器的安装、桥接生成，以及 Win64 Player、Android ARM64 真机和 iOS ARM64 模拟器已通过验证。三个 Player 目标均在相同原生二进制下执行两版外部 DLL，每版覆盖 AOT 补充元数据、热更结构体泛型集合、混合浮点与整数参数、结构体返回值和异常传播。Win64 的默认 `.NET Standard 2.1` 与 `.NET` API 配置、iOS 模拟器的默认配置使用 .NET 10 BCL；默认 Android 使用 Mono BCL。源码保留精确修订防护，配套工具包为匹配的安装生成 `HYBRIDCLR_UNITY7_EXPERIMENTAL`。升级编辑器时需要更新源码锁并重新验证。

在 Visual Studio x64 开发者环境中，先用配套的 `unity7/prepare_probe.py` 生成独立源码目录。`--with-toolchain` 同时复制当前编辑器的 IL2CPP 工具。`tests/unity7/verify.py --help` 提供对象编译、元数据解码和运行时源码清单检查；输出目录必须不存在，失败返回非零并保留完整日志。

运行 `tests/unity7/run_aot.py --help` 可查看独立 IL2CPP 验证参数。需要官方同版本 Windows IL2CPP 模块、准备好的完整 SDK，以及工具包 `Tests~/Unity7/build_bridge_host.py` 编译的桥接生成器。工具只写独立测试目录和明确指定的 SDK，不修改 Unity 安装或业务项目。机器有存储或构建调度规则时，应通过规定的构建包装器运行。
