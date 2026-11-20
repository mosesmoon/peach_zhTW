# ADR-0203：女优名称新增繁体中文，有 JavDB 繁体写法就显示繁体，没有显示日文

- 状态：已采纳
- 日期：2026-11-16
- 关系：扩展 [ADR-0153](0153-content-translations-live-beside-originals.md) 第六条的名称语言取值（`zh-CN`、`ja` 之外加 `zh-TW`），仍是只读投影；繁体界面语言见 [ADR-0201](0201-zh-tw-interface-language.md)；落库与撤回按 [ADR-0052](0052-entity-results-land-when-evidence-is-sufficient.md)，别名沿用 [ADR-0055](0055-performer-aliases-land-from-two-name-sites.md) 的批次号约定

## 背景

账本里女优的规范名是简体（`凉森玲梦`），由日文或 JavDB 的中文写法转来。繁体用户在「名称」里只有「中文」（简体）与「日文原文」两个选择，看不到站上本来就有的繁体写法（`涼森玲夢`）。JavDB 演员页的现名栏把中文写法与日文写法并列（`涼森玲夢, 涼森れむ`），简体界面下也不变（`peach.javdb` 记录过实测）；原先的取名脚本只取它转成简体后落库，繁体原文随即丢掉。

## 决策

**一、第三个取值。** `performerNameLanguage` 增加 `zh-TW`（设置里叫「繁体中文」）。选它时：该女优有来自 JavDB 的繁体写法就显示繁体，没有就显示日文原文。不拿简体规范名逐字转成繁体充数——运行期没有 OpenCC（它是可选依赖，不随安装档发行），逐字对照表也只覆盖日本字形；规范名本身没有日文对应时与 `ja` 一样保留当前名称。`zh-CN` 与 `ja` 的结果不变，规范名与作品署名不变。

**二、默认值。** 没选过时，界面语言是 zh-TW（含「自动」判成 zh-TW）用 `zh-TW`，其余用 `zh-CN`。名称语言存在账本的共享设置里，而「自动」的界面语言由每台设备的浏览器决定，服务端算不出有效值，所以：`GET /api/settings` 在没存过时回 `null`（以前回 `zh-CN`），前端用 `effectiveNameLanguage` 按页面的界面语言取默认，不回写。本机缓存的旧值若数据库里没有，同步时清成「没选过」（旧版本把默认值当选择缓存了）。用户存过的值一律不改。

**三、数据来源与判据。** 只采用 JavDB 演员页现名栏（`actor-section-name`）里整名皆汉字、无假名无拉丁的那一个，判据在 `peach.javdb.traditional_name`，沿用 `harvest_javdb_cn_names.py` 的三道闸，但因为运行期没有繁简转换，比脚本保守：

1. 页上的演员 id 必须就是已绑在该女优名下的那个（身份）；
2. 现名栏里的中文写法唯一，多于一个（站上把简体或日本字形也并了进来）不猜，按「查过、没有」记；
3. 日文名（或它自己）折叠日本字形后要落在账本名字链里，且日文名与它同姓；对不上就不采用。

搜索卡片的 `title` 是「全部写法」，混着日本字形与简体，分不出现名栏，所以不用；只读演员页。無碼那条记录常要登录，只进有碼那一页。JavDB 作品资料接口返回的演员名没有实测样本，这次不用。

**四、保存位置：别名加外部编号标记，不加迁移。**

- `entity_alias`：写法本身，来源 `auto:performer-zh-tw-name@<批次>`。搜索、搜索建议与 FTS 本来就读别名，繁体输入（如 `涼森玲夢`）因此找得到规范名为 `凉森玲梦` 的人；`entity_alias` 主键含来源，不与既有别名冲突。写法已被另一条女优占用时不写。
- JavDB 演员 id 那一行 `entity_external_ref.metadata_json`：`zh_tw`（空串表示查过、没有可用写法）、`zh_tw_for`（写入时的规范名）、`zh_tw_rule`。繁体写法属于 JavDB 现名那个艺名，用户之后改选别的艺名当规范名，它就不再显示（回落日文），别名仍可搜。

该来源不算艺名来源：页头「其它」组、可选规范名、`display_aliases`、补别名与补资料后继的名字链和指纹、种子包导出都跳过它；来源串不含 `javdb`，不会被 `entry_links` 当作可信艺名。

**五、显示。** 名称投影 `performer_name_display.display` 的 `choices` 与 `groups` 多一个 `zh-TW` 键（当前艺名用繁体写法，其余艺名用日文），`current` 与 `/api/entity/shapes` 的 `name_variants` 多 `zh_tw` 字段。前端 `entityDisplayName` 在 `zh-TW` 下取 `zh_tw`，没有取 `ja`，再没有取原名；不走日文转简体的字形表。演员页标头沿用 ADR-0069 的「中文名／日文名」分组，选 `zh-TW` 时分组读 `groups['zh-TW']`。

**六、补齐存量，限流不变。**

- 升级补修 `javdb-zh-tw-names-1`（`upgrade_rules.JAVDB_ZH_TW_NAMES`）：只读本机已缓存的演员页，不出网；缓存里没有页的 id 不记。按回执批次撤回：`revert_auto_landing.py --source auto:performer-zh-tw-name`。
- 补女优资料后继（`performer_profile_followup`）：新绑 id 时、以及已绑 id 没按现行判据查过时，用同一份 `pages`（同缓存、同 5 秒间隔、同冷却与登录墙处理）取一次有碼演员页。查过的标记进指纹，只对绑着 JavDB id 的女优生效，没有 id 的指纹不变。代价：存量里绑着 JavDB id 的女优各被重派一次，其余站的页走 30 天缓存。
- 撤回别名时同时清掉对应实体上的 `zh_tw*` 标记。

## 后果

- 繁体中文用户看到 JavDB 的繁体写法，找不到时看到日文，不会看到简体。
- 日文名全是汉字的女优，现名栏常有两个全汉字值（日本字形与繁体），按第三条第 2 点会回落日文；日后若要处理，需要可靠的繁简判别，另立决定。
- 规范名与日文名在账本里对不上的女优（没有保留日文原名）不写繁体，同样回落。
- `GET /api/settings` 的 `performerNameLanguage` 可能是 `null`，调用方要自己取默认。

## 2026-11-21 修订（合并上游 0.60.0）

上游 0.59.0（#682）把「女优名称」扩成五种显示方式，合并后本 ADR 的第一、二、五条按下面改读；第三、四、六条（数据来源、保存位置、补齐存量）与后果不变。

- **取值现为六个**（`web_settings.NAME_LANGUAGE_CHOICES`、`frontend/src/core/entity-names.ts` 的 `NameLanguage`）：`zh-CN`（中文化译名）、`zh-TW`（繁体中文，本 fork 新增）、`ja`（日语原文）、`en`（英文罗马音）、`ja-local`（日语原文（本地语言））、`local-ja`（本地语言（日语原文））。`ja-local` 与 `local-ja` 把两种写法并排，相同或取不到时只留一种，中文界面用全角括号。第一条里选 `zh-TW` 的结果不变：有 JavDB 繁体写法显示繁体，没有显示日文原文，不拿简体名逐字转繁体。
- **「本地语言」跟界面语言走**（`entity-names.ts` 的 `local()`）：简体中文界面是译名，日文界面是原文，其余界面是罗马音；**繁体中文界面是 JavDB 的繁体写法（`zh_tw`），没有繁体写法时退回日文原文**，同样不做简转繁。这是上游「本地语言」规则在 zh-TW 界面下的 fork 版本。
- **默认值（第二条）仍按设备决定。** 没存过时 `GET /api/settings` 回 `null`，前端 `effectiveNameLanguage` 按页面界面语言取：zh-TW 界面用 `zh-TW`，其余用 `zh-CN`；存过的值一律不改。
- **第五条的分组读法已变。** 演员页标头的「中文名／日文名」分组现在读 `name_display.groups[nameScript()]`，`nameScript()` 只返回 `zh-CN` 或 `ja` 两套（`entity-hero-page.tsx`）：`zh-CN` 与简体界面下的 `local-ja` 读中文那套，其余（包含选 `zh-TW` 与繁体界面的 `local-ja`）读日文那套。因此「选 `zh-TW` 时分组读 `groups['zh-TW']`」不再成立；`groups` 里仍有 `zh-TW` 键（`performer_name_display.py`），只是标头不读它。名称投影的 `choices` 与 `name_variants.zh_tw` 不变。
