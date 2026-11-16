# ADR-0205：AVWikiDB 作品页作为社区来源，补素人演员与有码空栏

- 状态：已采纳
- 日期：2026-11-16
- 关系：对 [ADR-0044](0044-scraping-stack-converges-to-two.md)「聚合站不再自写解析器」开一处例外；补充 [ADR-0067](0067-performer-profiles-land-in-their-own-table.md) 第五条的适用面（作品页进采集链，但演员编号仍不经作品页登记）；补充 [ADR-0145](0145-amateur-chain-asks-the-name-wikis-for-the-cast.md)（素人链认人来源多一家）；沿用 [ADR-0033](0033-online-sources-only-fill-empty-fields.md)、[ADR-0034](0034-lone-community-source-fills-and-javdb-settles.md)、[ADR-0038](0038-field-priority-chain-settles-dissent.md) 的补空与优先序

## 背景

`avwikidb.com` 此前只在补女优资料与补头像后继里用：作品页的 JSON-LD 给演员编号，女优页给生日与身高（ADR-0067）。2026-11-16 的评估对 SSIS-001、259LUXU-1000、ABW-358 取了整页：

- 一般 GET 就回完整 HTML，`__NEXT_DATA__` 的 `pageProps.movie` 带厂牌、系列、导演、片长、完整类别与分开的男女演员，比 JSON-LD 全。
- 站方自述作品资料来自 FANZA 官方 API，MGS 一侧另行汇入。标题、厂牌、系列、类别、片长因此与 r18.dev、DMM、MGStage 是同一份底层数据。
- 站上独有的是演员：官方没署名的作品，站方按包装印字、同作别号与人工比对认出演员，并用 `actorUnknown` 标出。站方自述已认出约 23 万部素人作品，本机没有准确率数据。
- 作品资料里的日期是配信日。MGS 一侧的有码作品（ABW-358）标题还带商店附注。

素人链缺演员时只有两个 Wiki 能答（ADR-0145）；有码链在 r18.dev 与 DMM 都落空时，下一站是综合索引，而综合索引不给片长。

## 决策

**一、作品页成为社区来源，窄用。** 新增来源 `avwikidb`（`sources/avwikidb.py`，解析器名 `avwikidb-work`），分级 `community`，只读 `pageProps.movie`，不做 JSON-LD 回退。它有两个位置，别的内容类型都不问：

- 素人链：`mgstage → sougouwiki → av_neme → avwikidb → avbase → javbus → javdb → r18dev`。缺演员时接在两个 Wiki 之后，沿用 ADR-0145 的短路：任一认人来源给出演员就不再问下一个，都没给时 MGStage 的字段够了就停，不落到综合索引。
- 有码链：`… → r18dev → dmm → avwikidb → avbase → javbus → javdb`。自成一档，前面的档给齐必填标量就不问它；它只在前面都落空时补空，而且它答完不让 `settles` 短路（`metadata_routes.echoes`）：它与 r18.dev、DMM 同源，只是转述，综合索引照问，不让转述顶替它们的表态。

无码、FC2、MIB、`other`、`unsure` 不问：这些类型站上的涵盖范围没有实证（猜测的 FC2、日期式番号都是 404，只证明那几个番号不存在）。

**二、同源的标量不算第二家印证。** 标量字段与官方来源同源，两者一致不是两个独立声音。`metadata_policy.REPUBLISHING_SOURCES` 登记这类来源；`independent_sources` 在自动落库记「几家一致」时不计它，至少算一家（`agreed_sources` 与规则名里的「N 家一致」据此）。站方认出的演员例外，那是它独有的判断。它仍按 ADR-0033 只补空，社区来源不覆盖已有值；在字段优先序里排在 javdb 之后、javbus 之前，永远不压过官方来源（`FIELD_SOURCE_ORDER`）。演员栏不加进 `FIELD_SOURCE_PRIORITY`：没有准确率数据，不让它排到官方档前面。

**三、站方认出的演员单独不自动落库。** 采集时 `actor_unknown` 为真的演员候选标 `site_identified`。`metadata_auto_apply._without_unbacked_identification` 把这样的候选从补空证据里拿掉，除非 `metadata_policy.IDENTIFYING_SOURCES`（素人系総合 Wiki、av_neme、av_name）里另一家给出同一批人。候选仍在行里，进人工复核。没有任何认人来源开过口时，这一行的演员整栏不自动落：留着 MGStage 的素人名义自动补空，站方认出的艺名就再也进不了复核（栏位非空后采集不再生成候选）。有认人 Wiki 给了别的人时听 Wiki，站方那份单独丢掉。`scripts/scrape_codes.py` 自己摊候选，用同一个标记。官方署名的演员（`actorUnknown` 为假）按普通社区来源补空。链上两个 Wiki 都没答才会问到它，所以实际上它给出认人结果的素人片，演员栏多数进复核，要等准确率抽样再放宽。

**四、演员不带编号，封面留空。** `performers` 只给 `japanese_name`，不放 `external_id`：`metadata_auto_apply` 落库时会把它登记成外部编号，等于绕过 ADR-0067 第五条「名字或罗马字恰好一位对得上才绑」。编号仍由补女优资料后继从 JSON-LD 出演表取。`cover_urls` 留空：图本体是 DMM／MGS 的图，封面层已独立持有，转载地址放进来会被 ADR-0032 的图源互证误算成第二个图源。

**五、不采用的字段。** 站方改写的 `summary`、`reviewSummary`、`reviewAverage`；样片网址（不取用影片）；`/mgsimg/` 站内图片路径与 `/api/`、`/go/`（robots.txt 对这三处禁止，`/mgsimg/` 还对 AI 相关爬虫点名）；`relating`、`similarSection`。`amateurProfile` 的自报名与年龄没有消费者，也不取。

**六、MGS 底的非素人作品。** `floor` 是 `videoa`（DMM 数字版）、`videoc`（素人版），或番号属素人时，才填标题与发行日。其余（`floor` 为 `mgs` 的有码作品，如 ABW-358）标题带商店附注、日期是配信日：标题留空，日期记进 `extra['delivery_date']`，与 `metadata_amane` 对 Prestige 的做法一致。日期是 UTC 时间，换成日本时间再取日。

**七、限流与冷却。** 主机间隔 3 秒，冷却键 `avwikidb`（`scraping_access.SOURCES`，拒绝访问先停 15 分钟、翻倍到 6 小时）。作品页来源走资料处理的 `HostLimitedTransport`，补女优资料与补头像后继的 `avwikidb_pages` 改为等同一个 `library_processing.SOURCE_LIMITER`，两条线同时跑时对 avwikidb.com 的合计速率仍是每 3 秒一页。两边的冷却记录是否同一份取决于资料处理的凭据根（`config.directory('secrets')`）与后继的 `follow_secrets_root`（默认 `SECRETS_DIR`）是否同一个目录；测试只在两者相同时验证了共享，部署上这两个路径来自同一份数据根，但没有逐一核对。页缓存仍是两套：后继的 `provider-cache/avwikidb-pages` 与采集的来源快照 `library-metadata/<番号>-avwikidb.json`，同一部作品可能各取一次。

## 理由

- 站方认出的素人演员是本机现有来源没有的信息，与 ADR-0145 的两个 Wiki 同类，位置照搬。
- 有码链上它的价值是补空：片长是 AVBase 不给的，系列、厂牌、导演在前面落空时也能补；放在 dmm 之后、综合索引之前，既不占 `LIST_FIELD_DEPTH` 的名额，也让 `settles` 在前面已齐时不问它。
- 同源不算印证，是因为 ADR-0030 的免复核门槛想要的是两个独立来源；把转载算进去，会让一份 DMM 数据的两次转述看起来像两个证据。
- 窄做、不做回退：JSON-LD 少厂牌、系列，类别也是过滤后的子集，两套解析各有缺口，不如只认一份结构。

## 被否决的方案

- **并进 `WIKI_STAGE`。** `LibraryMetadataProvider.wiki` 以 `WIKI_SOURCES[source]` 取站，会 `KeyError`；改用独立的 `CAST_STAGE`（`WIKI_STAGE` 加 `avwikidb`）。
- **并进 `COMMUNITY_STAGE`。** 会占 `LIST_FIELD_DEPTH=3` 的名额，并改变 ADR-0030 想要的互证样本。
- **走 amane 桥。** amane 没有这个站，且站上的演员编号与辨识标记是 Peach 特有的需求；自写解析器沿用已有的 `avwikidb.py` 读法，没有新增依赖。
- **站方认出的演员单独补空（比照两个 Wiki）。** 没有准确率数据；Wiki 的 29 部样本不能替它背书。
- **演员带 `external_id`（比照 fc2cmadb）。** 绕过 ADR-0067 第五条。
- **MissAV。** 同次评估中作品页回 Cloudflare 验证页，依任务规则停止、未尝试绕过；不接入。

## 后果

- 素人缺演员且两个 Wiki 都没答时，每部多一次 avwikidb 请求；有码片 r18.dev 与 DMM 都没有时多一次。
- 有码链上前面都落空时，AVWikiDB 即使给齐必填标量，综合索引也照问，所以那一行多一次请求。素人链上不受此限，认人来源给齐就停，不落到综合索引。
- 两个 Wiki 都没答、而 AVWikiDB 认出了演员的素人片，演员栏改为人工复核；此前这类行由 MGStage 的素人名义自动补空。
- 「封面没有」的记忆以链上能给封面的来源为前提，AVWikiDB 不给封面，列进 `metadata_routes.COVERLESS_SOURCES`，接上它不会让已记下的封面记忆作废。
- 站方认出的演员多数会进人工复核；准确率抽样（建议 29 部以上、不同厂牌，对照账本已确认演员与两个 Wiki）完成后，再决定要不要把它放进 `FIELD_SOURCE_PRIORITY` 或放宽单独落库。本 ADR 没有这份数据。
- 个人营运的单点站，站方改版会让 `__NEXT_DATA__` 结构变动，解析器回 `parse_error`（不可重试），不会静默回空。
- 未验证：项目实际出口与代理下的可达性（录制样本只经 `SourceTransport` 取了 5 次页，全部 200 或 404）；`/legal/` 与使用条款对自动化的态度（评估时未读）；`_needsDisambiguation` 为真时的页面形状；MGS 版有码作品除 ABW-358 外与 MGStage 的逐笔对照。
