# ADR-0201：登记 zh-TW 为第三种界面语言，中文标签按文字与地区分流

- 状态：已采纳
- 日期：2026-11-15
- 关系：修订 [ADR-0156](0156-interface-translation.md) 里「中文的各种写法都算简体中文」「语言名称用各自语言的自称（简体中文、English）」两处，并说明其「加第三种语言时改成按语言拆分动态载入」暂不执行；资源位置与回落沿用 [ADR-0159](0159-interface-text-lives-only-in-locale-resources.md)

## 背景

ADR-0156 只登记了 zh-CN 与 en，所有中文标签（`zh-TW`、`zh-Hant-HK` 等）都落到简体中文。繁体中文用户因此看不到自己的字，浏览器与系统明明报的是繁体。

## 决策

**一、登记。** `zh-TW`（台湾正体中文）成为第三种界面语言。前端 `INTERFACE_LANGUAGES` 与后端 `web_settings.INTERFACE_LANGUAGES` 一起登记，顺序是 `zh-CN`、`zh-TW`、`en`。设置里的选项自称「繁體中文」，不随界面语言翻译。

**二、中文标签分流。** 前端 `matchInterfaceLanguage` 与后端 `system_language.interface_language` 是同一条规则的两份实现，两边的测试用同一组案例：

1. 先去掉 `.编码` 与 `@修饰`，`_` 当 `-`，不分大小写。
2. 主语言不是 `zh` 的，只认 `en`，其余没有对应。
3. 是 `zh` 时，文字子标签优先于地区：含 `Hant` 给 `zh-TW`，含 `Hans` 给 `zh-CN`。
4. 都没有文字子标签时看地区：`TW`、`HK`、`MO` 给 `zh-TW`，其余（没有地区、`CN`、`SG`、`MY` 等）给 `zh-CN`。

例：`zh_TW.UTF-8`、`zh-Hant-CN`、`zh-HK` 给 `zh-TW`；`zh`、`zh-Hans-TW`、`zh-SG` 给 `zh-CN`。文字优先是因为 `zh-Hant-CN` 说的是写法，`zh-Hans-TW` 同理，地区只说明用户在哪里。

**三、资源由脚本产生。** `resources/locales/zh-TW/` 与 `scripts/locales/zh-TW/dev.json` 由 `scripts/build_zh_tw_locales.py` 自 zh-CN 转换产生（OpenCC `s2twp`，再做术语后处理），审校只改 `scripts/zh_tw/overrides/` 与 `scripts/zh_tw/terms.json` 里的逐键覆写，不手改产物。缺键仍按 ADR-0159 回落 zh-CN。

**四、暂不按语言拆分载入。** ADR-0156 预告加第三种语言时拆包。zh-TW 的资源与 zh-CN 大小相当（约 0.5 MB），全部打进主包会让主包再大约 0.5 MB。这次仍打进主包：拆包要把模块顶层同步取文案的代码改成异步，范围远大于登记一种语言。主包体积成为问题时另立 ADR。

**五、更新说明。** GitHub Release 正文由本 fork 的发布流程产生，除英文正文和折叠的「简体中文」段外，另有折叠的「繁體中文」段。繁體段在产生正文时由简体段转换（`scripts/changelog.py` 复用 `scripts/build_zh_tw_locales.py` 的 OpenCC 与 `scripts/zh_tw/terms.json`，用词与 zh-TW 界面一致），放在完整变更链接之后，只认英文与简体段的旧版应用读到链接就停，不受影响。应用没有随包分发的简转繁能力（OpenCC 只在可选依赖 `naming` 里），所以转换只发生在发布时，不在用户机器上；缺 opencc 时 `changelog.py --notes` 报错，不静默省略。`release_updates.changelog_notes` 解出 `en`、`zh-CN`、`zh-TW` 三份，没有繁體段（上游格式、旧版 Release）时 `zh-TW` 与 `zh-CN` 相同；前端 zh-TW 界面取 `zh-TW`，缺则取 `zh-CN`。

**六、其他随语言变的地方。**

- 在线字幕：中文界面（简体、繁体）都搜 `zh`，服务端同时搜简体与繁体字幕。
- 播放器：Video.js 的 `locales/zh-TW.js` 一起 vendor，播放器根元素的 `lang` 是 `zh-TW` 时取用。
- 中文名字排序：繁体界面按 `zh-TW`（笔画序），其余界面沿用 `zh-CN`；按数据键排序的地方不随界面变。

## 后果

- 繁体中文的浏览器与系统自动得到 zh-TW，托盘、命令行与服务端页面同样。
- 地区是 `CN`、`SG`、`MY` 的繁体用户若没有 `Hant` 标签，仍得到简体，可以在设置里固定。
- 字型与安装程序不在本 ADR 范围。
