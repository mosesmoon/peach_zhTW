# 台湾圆体 TaiwanPearl 2.125（子集）

- 上游：台湾圆体 TaiwanPearl 2.125（Chun yu Yao，基于思源黑体与小杉圆体），文件 `TaiwanPearl-Regular.ttf`，SHA-256：`51B3C9A4AB1B6B45DCDAD7C5AE93386AEA399FD3DABB85D2AC41110DC57F211D`。
- 许可证：SIL Open Font License 1.1，见同目录 `LICENSE`（版权声明取自字体 name ID 13，后接许可证原文）。
- 保留字体名称（Reserved Font Name）：`TaiwanPearl`。子集化属于「修改版」，按许可证第 3 条，所有对外名称记录（name ID 1、3、4、6）已改为 `Peach Round TC`，CSS `font-family` 同名；版权与许可证记录（name ID 0、13、14）原样保留。
- 生成：`scripts/build_taiwan_pearl_webfont.py`，命令见脚本文件头。不是 npm 包，不由 `npm run vendor:web` 生成或校验，也不进依赖清单。
- 分段：36 段 woff2（`segments.tsv` 逐段列出字符数、字节数与 SHA-256）。`base` 为拉丁、标点、注音、假名与符号；`hangul-*` 为韩文音节；`common-*` 为 Big5 A440–C67E 常用字（约 300 字一段）；`secondary-*` 为 Big5 次常用字（约 1100 字一段）；`rest-*` 为其余汉字（约 2500 字一段）。合计 8543908 字节，浏览器只下载页面用到的段。
- `index.css` SHA-256：`C5A8D8AA2B579CA41F9B9091997C06E69C8A1207D35DE02E3AC9A0B8BA557943`；`segments.tsv` SHA-256：`198E5463565D6D4FDC51E999658A34CA2E4A0D74AF65BBF4FFFC31DE31BBF5C5`。
- 只有 Regular 一个字重，`@font-face` 声明 `font-weight: 400`：500 显示为常规字重，600 以上由浏览器合成粗体。
- `/vendor/` 以一年 immutable 缓存。woff2 文件名带内容哈希；重新切分时必须同时换版本目录，不要原地覆盖 `index.css`。

使用处：`frontend/src/i18n/index.ts`（界面语言为 zh-TW 时挂 `<link>`）、`web_entry.page_shell`（仅 zh-TW 页面），字体栈见 `frontend/src/react/base.css` 与 `web/board.css` 的 `:root:lang(zh-TW)`。
