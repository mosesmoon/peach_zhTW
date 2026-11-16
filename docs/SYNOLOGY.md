# Synology 套件（SPK）

本文说明如何为群晖 NAS 构建并手动安装 Peach 的 SPK 套件。套件是这份 fork 自行封装的社区版本，不是 Synology 或上游的官方套件。它不使用 Docker 或 Container Manager，Peach 以套件专属的低权限用户运行无桌面服务（`python -m peach.server`，见 [ADR-0105](adr/0105-linux-headless-container.md)）。封装决策见 [ADR-0204](adr/0204-synology-spk-packaging.md)。

2026-11-16 的构建与静态检查在 Windows 开发机完成，没有在任何 Synology 设备上安装或运行过；[未在实机验证的项目](#未在实机验证的项目)必须先读。

## 支持范围

| 项目 | 说明 |
| --- | --- |
| 处理器 | 只支持 x86-64 机型。INFO 的 `arch` 写 `x86_64` 加上 pkgscripts-ng 归入 x86_64 家族的全部平台代号（apollolake、geminilake、denverton、broadwell、v1000、r1000、epyc7002 等），不含任何 ARM 平台 |
| DSM 版本 | DSM 7.2 及以上（INFO 声明 `os_min_ver="7.2-64561"`）；不支持 DSM 7.0、7.1 与 DSM 6，原因见下一节 |
| 运行环境 | 套件自带 CPython 3.14（python-build-standalone）与锁定的 Python 依赖，不依赖系统 Python |
| FFmpeg | 套件不含 FFmpeg，需自备并在安装向导指定，见 [FFmpeg](#ffmpeg) |
| 应用内更新 | 不可用。更新靠安装新版 SPK |

### glibc 下限

套件里的原生库来自 Linux x86-64 wheel。构建脚本会扫描所有 ELF 文件中的 `GLIBC_x.y` 符号，实测最高为 2.27（来自 numpy 与 Pillow），`GLIBCXX` 最高为 3.4.21。Synology 工具链的发布文件名记录了各版本的 glibc：DSM 7.0 与 7.1 为 2.26，DSM 7.2 为 2.36（`archive.synology.com/download/ToolChain/toolchain/` 的 `gcc*_glibc*` 文件名，2026-11-16 查阅）。

因此套件的 `preinst` 在 glibc 低于 2.27 时拒绝安装并给出提示：**可用的是 DSM 7.2 及以上**。INFO 的 `os_min_ver` 已声明 7.2，套件中心会直接把 DSM 7.0 与 7.1 标为不兼容；`preinst` 的 glibc 检查留作第二道保险。Pillow 是核心依赖，去掉可选的 OpenCV 与 NumPy 也不能解决。

## 构建

在仓库根目录的任一系统上（Windows 即可）：

```sh
uv run --no-sync python scripts/package_synology.py --dry-run   # 只解析并列出要下载的文件
uv run --no-sync python scripts/package_synology.py             # 构建
```

- 版本取 `peach.__version__`，输出 `build/synology/Peach-<版本>-x86_64.spk`；`--revision` 修改 INFO 里的构建号（默认 `0001`）。`--without-vision` 不带 OpenCV 与 NumPy（人脸功能）。
- 依赖版本以 `uv.lock` 为准：`uv` 按 Linux x86-64 求解要装哪些包，脚本再从锁文件选出每个包的 wheel，下载前打印文件名、地址与大小，并核对锁文件里的 SHA-256。没有可用 wheel 时中止，不改用其他版本。
- 只访问两个来源：python-build-standalone 的 GitHub Release（`astral-sh/python-build-standalone`，固定在发布 `20261110`，哈希写在脚本里并与官方 `SHA256SUMS` 一致）与 PyPI 文件站。下载缓存在 `build/synology/cache/`。
- 构建结束自动做静态检查（结构、INFO、脚本、权限、ELF 架构、Windows 专用文件、个人路径），有问题时以非零状态退出。
- 套件体积较大（约 160 MB，解开约 440 MB），主要来自 OpenCV 与 NumPy。

## 安装

1. 在 DSM 打开「套件中心」。该套件没有 Synology 签名，需要先在套件中心右上角「设置」的「常规」里，把「信任级别」设为允许任何发行者（DSM 7 的措辞以实际界面为准），安装完成后可改回。
2. 点「手动安装」，选择 `.spk`。
3. 安装向导第一页填：
   - **媒体文件夹路径**：NAS 上存放影片的完整路径，例如 `/volume1/video`。
   - **网页端口**：1024 到 65535，默认 8900。套件不能使用 1024 以下的端口。
4. 第二页填访问密码（8 到 256 个字符，必填）和选填的 FFmpeg 文件夹。
5. 完成后套件自动启动，在 DSM 桌面或主菜单会有 Peach 图标；也可以直接打开 `http://<NAS 的 IP>:<端口>`，用刚才的访问密码登录。

向导里的访问密码经由 `postinst` 只用来写入 Peach 的访问设置（Peach 自己以哈希保存），不会写入套件的配置文件。套件首次安装时由 `scripts/synology/provision.py` 用与网页首次设置相同的 `onboarding` 代码写入设置文件：媒体目录登记为本地来源，数据库路径前缀为 `R:\media`（见 [OPERATIONS](OPERATIONS.md) 的媒体路径说明），实际目录映射到向导里填的路径。

## 授权共享文件夹

DSM 7 的套件不以 root 运行，套件用户 `PeachZhTW` 默认读不到任何共享文件夹。安装后（或在首次扫描前）：

1. 控制面板 →「共享文件夹」→ 选中存放影片的共享文件夹 →「编辑」→「权限」。
2. 把顶部的下拉选单从「本地用户」改为「系统内部用户」。
3. 找到 `PeachZhTW`，勾选「只读」（只扫描与播放）。需要整理、移动或删除影片时才勾「读写」。
4. 保存。若文件夹里有单独设了权限的子文件夹，也要对它们授权。

套件没有使用 `data-share` 资源：它只接受固定的共享文件夹名称，并且会在名称不存在时新建共享文件夹，不适合让使用者自己填路径。

## 设置媒体路径

安装向导已登记第一个媒体文件夹。要增加或修改：在 Peach 的「配置」页「媒体目录」里添加 NAS 上的路径（例如 `/volume1/video`），Peach 的目录选择器浏览的是套件用户看得到的目录，所以要先完成上节的授权。

## FFmpeg

套件不含 FFmpeg。缩略图、预览与转码需要 `ffmpeg` 与 `ffprobe`；MP4 等浏览器可直接播放的格式不受影响。

- 在向导第二页填「FFmpeg 文件夹」，套件把 `<文件夹>/ffmpeg` 与 `<文件夹>/ffprobe` 写入数据目录旁的 `peach.conf`，启动时作为 `PEACH_FFMPEG`、`PEACH_FFPROBE`（见 `src/peach/ffmpeg.py`）。
- 之后要改，编辑 `/var/packages/PeachZhTW/var/peach.conf` 的 `PEACH_FFMPEG`、`PEACH_FFPROBE` 两行（需要 root 或 DSM 提供的方式），再重新启动套件。
- 套件用户必须对这个文件夹有读取与执行权限。
- 没有设置时，Peach 还会依次找数据目录 `tools/ffmpeg/bin` 与 `PATH`。DSM 自带的 FFmpeg 功能与是否带 `ffprobe` 未验证。

选用哪一种来源见 [ADR-0204](adr/0204-synology-spk-packaging.md)。

## 数据位置、升级与卸载

- 所有数据在 `/var/packages/PeachZhTW/var/`：`data/`（Peach 数据目录，含设置、数据库、凭据）、`peach.conf`、`log/peach.log`（超过 10 MB 轮替一次）、`log/provision.log`。
- 升级：在套件中心对已装的套件再次「手动安装」新版 SPK。`var/` 由 DSM 保留，`postinst` 看到已有 `peach.conf` 就不会重写向导值，也不会改动设置文件；`preupgrade` 另存一份 `config.toml.preupgrade`。数据库迁移在服务启动时由 Peach 自己执行。升级前建议备份 `data/`。
- 卸载：DSM 7 在卸载套件时通常删除 `var/`，其中包含 Peach 的数据库与设置。**这一点未在实机验证**，卸载前请先复制 `data/`。重新安装时向导会再问一次；若把备份的 `data/` 放回原位，其中的设置文件已存在，`provision.py` 不会改写它（访问密码与媒体目录沿用备份里的值，向导里填的这两项不生效）。
- 共享文件夹里的影片文件不受安装、升级或卸载影响。

## 已知限制

- 没有应用内更新、没有托盘、没有 mDNS（`peach.local`）发布。
- 元数据桥（amane）的独立运行环境没有随套件提供，相关功能不可用。
- 套件内的 OpenCV 轮子自带 FFmpeg 动态库，只供 OpenCV 内部使用，Peach 的媒体工具仍然调用上面设置的外部 `ffmpeg`。
- 人脸模型由 Peach 按需下载，需要能出网。
- 遥测与问题回报端点沿用代码里的设置，见 [ADR-0202](adr/0202-update-source-is-the-fork-github-releases.md) 末尾。
- 只做了防火墙以外的最小服务：未登记 `port-config`，若启用了 DSM 防火墙，需手动放行所选端口。

## 未在实机验证的项目

以下均只做了静态检查或隔离测试，没有在 DSM 上跑过：

- 套件能否被 DSM 7.2 接受安装（INFO 字段、`arch` 取值、无签名安装提示的措辞、`conf/privilege` 格式）。
- 向导的字段类型与校验，以及 `postinst` 能否在包用户下读到 `wizard_*` 变量。
- Python 与全部原生库在 DSM 上能否加载（glibc 与 `libstdc++` 版本、CPU 指令集、`/tmp` 与 `noexec` 挂载）。
- `start-stop-status` 的后台启动、停止与状态判断，端口占用与日志轮替。
- 桌面快捷方式（`ui/config` 的端口改写在 `postinst` 里执行，失败会被忽略）。
- 共享文件夹授权后的读取、整理与删除，以及 Peach 目录选择器在 DSM 上看到的目录。
- 卸载时 `var/` 是否保留，升级时 `var/` 是否保留（按 DSM 文档推定）。
- 访问密码在 DSM 套件安装日志中是否出现。

最可能出问题的地方：向导或 `ui/config` 的格式与 DSM 版本的细微差异；共享文件夹没授权导致扫描不到影片；没有 FFmpeg 导致缩略图与转码不可用。
