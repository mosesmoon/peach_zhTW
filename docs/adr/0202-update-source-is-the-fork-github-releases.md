# ADR-0202：应用更新来源改为本 fork 的 GitHub Release

- 状态：已采纳
- 日期：2026-11-16
- 关系：修订 [ADR-0012](0012-version-and-update-boundary.md) 之后各 ADR 里「GitHub 与上游下载站互为备援」的来源；沿用 [ADR-0137](0137-release-sums-ed25519-signature.md) 的签名机制与 [ADR-0127](0127-verified-release-artifact-promotion.md) 的发行产物约定；macOS 部分补充 [ADR-0130](0130-macos-sparkle-in-app-update.md)，Docker 部分不改 [ADR-0140](0140-docker-one-click-update-via-watchtower.md)

## 背景

这份 fork（`mosesmoon/peach_zhTW`）打包的安装档若仍查询上游，会被「更新」成上游版本，失去 fork 的修改。上游的查询来源有三处：GitHub Releases、下载站 `downloads.peach.video` 的 `releases.json`、macOS 的 Sparkle appcast；Docker 另查 Docker Hub 的上游镜像。

## 决策

**一、版本清单与更新说明只取 fork 的 GitHub Release。** `release_updates.REPOSITORY` 是仓库 owner/name 的唯一出处，`RELEASES_URL`、`API_URL` 与 `release_notice.RELEASES_URL` 都由它组出，日后同步上游只需处理这一行的冲突。

**二、更新包只从 fork 的 Release 下载。** 下载站不再是清单来源，也不是下载备援：`download_sources()` 只回传原地址一个来源，调用方逐个尝试的写法不变。工具包（`tool_package`）与轻量安装器的工具下载走同一份列表与同一个来源。

**三、没有 Release 时不报错也不退回上游。** 列表为空或 API 回 404，检查结果是 `empty`（「暂未找到可下载的测试版」）；其他失败（403、429、5xx、网络错误）仍是 `error`。自动下载只在 `available` 时启动，因此也不会下载任何东西。`staleListing` 这条信息原本用于「只取到镜像」，现在不会产生，保留键是为了不动语系资源。

**四、macOS 暂不启用 Sparkle。** 上游的 appcast 只由 `sparkle-appcast` 作业上传到下载站，并用上游持有的私钥签名；`PUBLIC_ED_KEY` 是上游的公钥，fork 无法产生可验证的 appcast。因此 `FEED_URL` 为 None，`info_plist_keys` 不写 `SUFeedURL` 与 `SUPublicEDKey`，Sparkle 不启用，菜单栏沿用版本检查加 DMG 下载（DMG 来自 fork 的 Release）。要启用须：生成 fork 自己的 Ed25519 密钥并改 `PUBLIC_ED_KEY`、让发布流程产生并上传 appcast（Release 资产或自有主机）、再设置 `FEED_URL`；密钥变更须按 ADR-0130 先改 ADR。

**五、Docker 不比对镜像。** 这份 fork 不发布镜像，`docker_update.REPOSITORY` 留空：`published` 不询问任何镜像仓库，容器里检查到 fork 的新 Release 时只报「镜像尚未发布」，不提示 `docker compose pull`，也不给一键更新。`compose.yaml`、`nas_setup.IMAGE` 与文档里的 `longmeidao/peach` 是上游的 Docker Hub 命名空间，原样保留；按它们部署得到的是上游镜像。

**六、签名现状不变。** `release_signing.PUBLIC_KEYS` 仍为空，更新器不要求签名，摘要取 GitHub 资产的 `digest`。fork 要启用须生成自己的密钥、写入公钥、让发布流程为 `SHA256SUMS.txt` 产生 `.sig`（ADR-0137）；公钥写入后，缺签名的 Release 不会被安装。

## fork Release 须满足的条件

- 标签 `vX.Y.Z`（三段数字），非草稿；预发布可用。
- Windows：`Peach-X.Y.Z-windows-x64.zip` 必须有；有 `-update.zip` 且四个工具包 `-tools-<工具>.zip` 齐全时优先用更新包。资产状态须为 `uploaded`。
- macOS：`Peach-X.Y.Z-macos-<arm64|x86_64>.dmg`，只提示下载，不在应用内安装。
- 签名启用后另需 `SHA256SUMS.txt` 与 `SHA256SUMS.txt.sig`。
- 正文格式见 `scripts/changelog.py`：英文正文、折叠的「简体中文」段、完整变更链接，其后是折叠的「繁體中文」段（ADR-0201）；缺省则更新说明为空。产生正文需要 opencc（`uv sync --extra naming`），发布流程里调用 `changelog.py --notes` 的作业须安装它。

## 后果

- fork 没有 Release 时，更新检查显示「暂未找到」，不会指向上游。
- 上游发布流程（R2 镜像、appcast、Docker 推送）与 fork 无关；fork 自行发布时须调整 `release.yml` 等，本 ADR 不改发布流程。
- README 的下载链接与徽章、设置页写死的官网与 GitHub 链接、问题回报与遥测端点仍指向上游，另行决定。
