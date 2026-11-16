# ADR-0204：Synology 套件（SPK）自带执行环境，以低权限用户运行无桌面服务

- 状态：已采纳；构建与静态检查已做，实机验收未做
- 日期：2026-11-16
- 关系：沿用 [ADR-0105](0105-linux-headless-container.md) 的无桌面服务（`python -m peach.server`）与 [ADR-0023](0023-generic-distribution-roadmap.md) 的通用分发路线；更新来源沿用 [ADR-0202](0202-update-source-is-the-fork-github-releases.md)；用法见 [Synology 套件](../SYNOLOGY.md)

## 背景

使用者要在 x86-64 的 Synology NAS（DSM 7）上，不用 Docker 或 Container Manager，经套件中心「手动安装」运行这份 fork。DSM 没有 Python 3.14，也没有为 Peach 准备的 FFmpeg。

## 决策

**一、自带运行环境。** 套件内嵌 python-build-standalone 的 CPython 3.14（`x86_64-unknown-linux-gnu`，`install_only_stripped`，基线 CPU），加上 `uv.lock` 锁定的全部依赖（含 `vision` 额外依赖，与 Docker 镜像一致）的 Linux x86-64 wheel 与 Peach 源码。构建脚本 `scripts/package_synology.py` 只用标准库、`uv` 与 Pillow（取图标），在 Windows 上即可构建：不把 wheel 解到 NTFS，而是从压缩包直接写入 tar，显式设置 Unix 权限与 0:0 所有者。Python 执行环境与每个 wheel 都核对哈希（前者固定在脚本里并与官方 `SHA256SUMS` 一致，后者取自锁文件）。没有可用 wheel 时构建中止。

**二、glibc 下限由实测决定。** DSM 7.0、7.1 的 glibc 是 2.26，DSM 7.2 是 2.36（Synology 工具链文件名）。Pillow 与 NumPy 的 wheel 要求 glibc 2.27，所以脚本扫描所有 ELF 的 `GLIBC_x.y` 符号，把实测最高值写入 `preinst` 的检查；使用者据此把支持范围定为 DSM 7.2 及以上：INFO 写 `os_min_ver="7.2-64561"`，套件中心直接把 DSM 7.0 与 7.1 标为不兼容，`preinst` 的 glibc 检查留作第二道保险。

**三、`arch`。** 写 `x86_64` 与 pkgscripts-ng（`plat_to_family`）归入 x86_64 家族的全部平台代号，不含 ARM。官方附录表没有列 r1000、epyc7002、`nk` 变体，而 pkgscripts-ng 与 SynoCommunity 都有，所以以后者为准；字面 `x86_64` 是否被 DSM 接受没有一手证据，列出平台代号保证不依赖它。

**四、安装形态不设 `PEACH_DISTRIBUTION`，不改源码。** 设成 `docker` 会带来 `/media` 默认值、`docker compose` 步骤、更新令牌与「镜像未发布」提示，全部不适用。不设时：`in_app_update()` 在 Linux 为假，自动更新与 Windows 更新包下载都不会触发；`media_tools.supported()` 只在 Windows 为真，不会下载 Windows 工具包；`peach.server` 为子进程设置 `PEACH_HEADLESS_MANAGED=1`，配置页允许本机与私有网络的已登录客户端管理（`web_local_access.local_client`），NAS 上的浏览器因此可以改设置。代价：没有 Docker 才有的网页首次设置页，所以由 `postinst` 调 `scripts/synology/provision.py`，用与网页首次设置相同的 `onboarding.apply` 写入媒体目录与访问密码，避免「没有访问策略时只能用 `peach token` 的口令登录」的首次体验。

**五、权限与数据。** `conf/privilege` 为 `run-as: package`，用户与组均为 `PeachZhTW`。数据目录是 `SYNOPKG_PKGVAR/data`，DSM 升级时保留 `var`。共享文件夹由使用者在「控制面板 → 共享文件夹 → 权限 → 系统内部使用者」授权；不用 `data-share`，因为它只接受固定的共享文件夹名称、名称不存在时会新建，不能表达使用者填的路径。端口由向导决定并写入 `var/peach.conf`；INFO 是静态文件，不能写 `adminport`，桌面快捷方式用 `ui/config`，`postinst` 改写端口。

**六、FFmpeg 不随包。** 套件只让 `PEACH_FFMPEG`、`PEACH_FFPROBE` 指向使用者提供的位置（向导或 `peach.conf`），沿用 `src/peach/ffmpeg.py` 的解析顺序。三种来源比较：

| 来源 | 优点 | 缺点 |
| --- | --- | --- |
| DSM 自带 `/usr/bin/ffmpeg` | 零安装、已在 `PATH` | 版本旧、编码器受限、是否带 `ffprobe` 与 AV1 解码均未验证，Synology 随系统升级可能变动 |
| SynoCommunity 的 FFmpeg 套件 | 功能完整、含 `ffprobe`、有人维护更新，Peach 不负担再分发义务 | 使用者要另装一个第三方套件，路径随套件名与版本变化，未验证 |
| 随包附静态构建 | 一次安装即用 | 多为 GPL（含 x264 等时），再分发要提供对应源码与许可证；体积约数十 MB；要自行跟踪安全更新；Peach 以独立进程调用，不构成链接，但仍需履行义务 |

建议先采用 SynoCommunity 的 FFmpeg 套件（向导里填它的 `bin` 目录），确认可用后，再决定是否附静态构建。这一版没有下载或内嵌任何 FFmpeg。

**七、更新靠重新安装。** 套件不触发应用内更新；`silent_upgrade="yes"`，升级不再弹向导，`postinst` 见到已有 `peach.conf` 就不改动向导值与设置文件。

## 后果

- 套件约 160 MB（解开约 440 MB）。不需要人脸功能时可用 `--without-vision` 去掉 OpenCV 与 NumPy，但不能解决 glibc 下限，因为 Pillow 同样要求 2.27。
- 支持范围是 DSM 7.2 及以上。若日后要支持 DSM 7.0 与 7.1，需要 Pillow 的 manylinux2014 轮子（上游没有）、改用 glibc 2.26 可用的构建，或放弃该版本，由使用者决定；不在本 ADR 范围内放宽锁定版本。
- 构建与静态检查只证明包的结构与 ELF 架构、glibc 符号需求；没有任何实机运行记录，验收清单见 [未在实机验证的项目](../SYNOLOGY.md#未在实机验证的项目)。
- 元数据桥（amane）的独立环境不随包，相关功能不可用；元数据桥需要 `uv` 或打包环境，与本决定无关地留待后续。
