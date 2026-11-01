# Unity 7 原生移植

状态：原生适配未完成，不能用于发布。

基线为官方 `v6000.3.x-9.0.1`，与工具包 `v9.0.3` 的版本清单一致。实验目标仅为 Unity `7000.0.0a12`，修订 `8751f7c83ed7`。配套的 [il2cpp_plus 维护分支](https://github.com/mmm1h/il2cpp_plus/tree/codex/unity7-support) 从本机安装的 Unity 7 生成探测用源码树。

Unity 7 将 `Il2CppGenericClass.context` 改为 `class_inst`。本分支提供值类型上下文适配，保持调用期间的上下文有效，并替换解释器、字段布局、元数据和虚方法处理中的直接字段访问。反射名称使用运行时的 `Type::GetName`，类型加载异常调用适配新的双参数接口。

默认编译明确拒绝 Unity 7。源码探测必须显式定义 `HYBRIDCLR_UNITY7_EXPERIMENTAL`；该开关只允许检查未完成的代码，不表示运行时可用。Unity 7 的方法签名、成员 token 和接口分发表已经改变，`GlobalMetadata` 分发、解释器元数据表示、AOT 补充元数据以及加载入口仍需移植。

泛型上下文可执行测试、公共兼容接口的对象编译和运行时异常源码的对象编译已通过 Unity 7 的真实头文件检查。同一泛型与公共接口检查也通过官方 Unity 6.3 基线头文件回归。完整原生源码诊断仍失败，不能链接或运行热更新；这些检查不覆盖 Player、安卓或 iOS。

在 Visual Studio x64 开发者 PowerShell 中，设置以下环境变量后执行。`UNITY_IL2CPP_DIR` 指向安装目录的 `Editor/Data/il2cpp`，另外两个变量必须指向尚不存在的独立输出目录。

```powershell
python ../il2cpp_plus/unity7/prepare_probe.py --unity-il2cpp "$env:UNITY_IL2CPP_DIR" --hybridclr . --output "$env:UNITY7_PROBE_DIR"
python tests/unity7/verify.py --prepared-root "$env:UNITY7_PROBE_DIR" --unity-il2cpp "$env:UNITY_IL2CPP_DIR" --output "$env:UNITY7_LOG_DIR" --diagnose
```

验证器保留编译日志和 `report.json`，任一检查失败即返回非零。`--diagnose` 额外检查原生翻译单元；项目生成的 `MethodBridge.inc` 不会用占位代码替代，因此对应翻译单元会明确列为未覆盖。工具不安装运行时，不修改 Unity 安装目录或业务项目。
