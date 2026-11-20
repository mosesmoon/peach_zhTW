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

## 2026-11-21 修订（合并上游 0.60.0）

合并上游 0.60.0（自 0.58.0）后核对本 ADR，决策不变，补记三点现状：

- **登记的界面语言仍是 `zh-CN`、`zh-TW`、`en`。** 前端 `INTERFACE_LANGUAGES`（`frontend/src/i18n/index.ts`）与后端 `web_settings.INTERFACE_LANGUAGES` 没有因合并而增减。
- **上游新增的占位语言目录不接入。** 上游在 `resources/locales/` 下建了 `zh-Hant`、`ja`、`ko`、`es`、`vi`（Hosted Weblate 建立，各命名空间文件内容都是空对象 `{}`），0.60.0 的应用没有登记也没有读取它们。本 fork 的 `zh-TW` 仍由 `scripts/build_zh_tw_locales.py` 自 `zh-CN` 生成，**不使用 `zh-Hant`**，也不把 `zh-TW` 改名或并入它：`zh-Hant` 目前是空的，没有可用译文；改走 Weblate 也意味着放弃本 ADR 第三条的脚本生成与逐键覆写。将来上游的 `zh-Hant` 有了译文并登记为界面语言时，另立 ADR 决定与本 fork 的 `zh-TW` 如何取舍，不在这次合并里预先处理。
- **第五条「更新说明」随上游改动而收窄。** 上游 0.60.0 起检查更新只显示每版的「重点」分组，不再显示完整变更。`release_updates.changelog_notes` 仍解出 `en`、`zh-CN`、`zh-TW` 三份，每份是 `{title, text}` 列表；`zh-TW` 取自 Release 正文里折叠「繁體中文」段中的「重點」分组，没有该段或该分组时与 `zh-CN` 相同。上游的 `LISTING_RULE` 是 `source-aware-v3`（`notes` 只含每版重点、两份语言），本 fork 的 `notes` 多了 `zh-TW` 第三份，规则值记为 `source-aware-v4`（`release_updates.py`）。`scripts/changelog.py` 把简体中文段整段转成繁體后折叠，「重点」分组标题随之变成「重點」（`release_words.TRADITIONAL_HIGHLIGHTS`），`changelog_notes` 靠这个标题取出繁体条目。
