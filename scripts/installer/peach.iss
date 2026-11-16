; Peach Windows 安装包。由 scripts/build_windows.ps1 -Installer 调用 ISCC 编译：
;   ISCC /DAppVersion=<版本> /DSourceDir=<独立目录包 Peach\> /DOutputDir=<输出目录> peach.iss
; 装的内容与免安装包逐字节相同，安装器提供目录选择、开始菜单项和「应用和功能」里的登记。
; 自更新、开机自启、桌面图标和应用内卸载仍由 Peach 管，约定见 src/peach/desktop_installer.py。

#ifndef AppVersion
  #error 缺少 /DAppVersion
#endif
#ifndef SourceDir
  #error 缺少 /DSourceDir
#endif
#ifndef OutputDir
  #define OutputDir "."
#endif

[Setup]
; 与 desktop_installer.APP_ID 相同；改了它，已装的机器会并排出现第二份。
AppId={{02D9748A-78F6-4866-AC75-918177194DAB}
AppName=Peach
AppVersion={#AppVersion}
AppVerName=Peach {#AppVersion}
AppPublisher=Peach
AppPublisherURL=https://github.com/mosesmoon/peach_zhTW
AppSupportURL=https://github.com/mosesmoon/peach_zhTW
; 只装到当前用户：自更新在程序目录旁边建事务目录再整目录切换，Program Files 不可写。
PrivilegesRequired=lowest
DefaultDirName={userpf}\Peach
DisableDirPage=no
UsePreviousAppDir=yes
UsePreviousTasks=no
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
#ifdef LiteInstaller
OutputBaseFilename=Peach-{#AppVersion}-windows-x64-lite-setup
#else
OutputBaseFilename=Peach-{#AppVersion}-windows-x64-setup
#endif
SetupIconFile=..\..\resources\peach.ico
UninstallDisplayIcon={app}\Peach.exe
UninstallDisplayName=Peach
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=no
LanguageDetectionMethod=uilanguage
CloseApplications=yes
RestartApplications=no

[Languages]
; 安装语言跟随 Windows 显示语言（ShowLanguageDialog=no）；没有匹配项时用第一项，所以英文排最前。
; Inno Setup 先按语言编号精确匹配，再按主语言加代码页匹配：zh-MO 落到繁体。
; 香港（$0C04）与新加坡（$1004）的中文显示语言用英文，由 [Code] 的 InitializeSetup 处理。
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "cht"; MessagesFile: "ChineseTraditional.isl"
Name: "chs"; MessagesFile: "ChineseSimplified.isl"

[CustomMessages]
; 三种语言各一份，键相同；代码里一律经 CustomMessage 取用，%n 是换行。
en.StillRunning=Peach is still running and could not exit automatically. Quit Peach from the tray menu and try again.
en.TaskCheckFailed=Setup could not confirm the status of background tasks and has been canceled. Wait for the tasks to finish and try again.
en.MigrationFailed=The local database could not be updated to the new version, so Peach may fail after it starts. The backup made before the upgrade is in the database folder of the data directory, with a file name starting with ledger.pre-migrate-.
en.DataKept=Peach has been uninstalled. Settings, the local database and watch history are kept in %1 and can be deleted manually if needed. Media files are not affected.
en.DirectoryOverlapsData=The program folder cannot overlap the Peach data folder. Choose a separate program folder.
en.DirectoryNotDedicated=Choose an empty folder or an existing Peach installation folder. Uninstalling Peach removes the whole program folder.
en.DirectoryNotWritable=The current user cannot write to the program folder or its parent folder. Choose a location with write access so Peach can be installed and updated.
en.DirectoryLink=The program folder and the data folder cannot go through a folder link. Choose a regular folder.
en.DirectoryMove=Uninstall the existing Peach first (keeping your data), then choose the new installation folder.
en.ReportingFailed=The version statistics and error diagnostics choice could not be saved. You can choose again in first-time setup or Settings; a consent that was not saved does not turn uploads on.
en.LibrarySharingFailed=The collection and taste upload choice could not be saved. You can choose again in Settings.
en.TaskReporting=Send version statistics and error diagnostics (recommended): version, system information, a random instance ID, failure type, code location and number of occurrences
en.TaskUploadGroup=Data upload (can be turned off in Settings):
en.TaskLibrarySharing=Upload collection and preference details (anonymized)
en.RunStarRepo=Open the Peach repository and star the project
en.LibraryTitle=Collection and taste details upload
en.LibrarySubtitle=Used for research on the collection structure and preferences of the Peach user community.
en.LibraryIntro=Continuing means you agree to the details and participation status listed below being sent. To opt out, go back and clear the checkbox.
en.LibraryText=Videos: deduplicated video codes, ratings, likes, dislikes, watched, watch later, play counts, watch progress and manually added tags from the controlled list. Custom note tags stay on this computer.%n%nPreference summaries: counts of favorites, likes, dislikes and watches, and rating distributions, grouped by performers, creators, labels, series, manual tags, decade and length (videos with codes and entries without codes counted separately), plus the names of people and labels you added to favorites.%n%nCollection coverage: number of files, videos with codes and entries without codes. Entries without codes are only summarized on this computer.%n%nCapacity: over the last 7 and 30 days, the days with observed capacity, days with playback activity and days covered; current and peak data and cache usage, observed growth, and cache cleanup. Cleanup includes automatic and manual cache cleanup and excludes backups and logs; unavailable values are left empty and missing days are not filled in. Days with playback activity do not cover all daily use.%n%nRandom research ID: created at random for this instance after you agree, and used to link the collection, capacity and participation status during this authorization. It changes when you turn sharing on again; machine fingerprints and diagnostic IDs are not used.%n%nSending schedule: collection, preference and capacity snapshots at most once a week; at most one contact log a day for the enabled status, with the current week's snapshot ID, field version, raw and compressed size, and preparation and delivery status. When you turn sharing off, the background can still try once to send a minimal log containing only the random research ID, the off status, the required version and the UTC time, and then stops.%n%nVersion and period: Peach version, field version and UTC calendar week.%n%nNot uploaded: accounts, machine fingerprints, diagnostic IDs, internal row numbers, file names, paths, titles, media, URLs, search terms, and individual browsing or watch records. Being offline, uninstalling and failed sends do not count as turning sharing off, and the number of research instances is not the number of people.%n%nThe full details can reflect adult content preferences; the receiving service is a separate Sentry project and can see the connecting IP.%n%nYou can view the full local preview or turn sharing off in Settings. After that, no more research details are sent, and only the single minimal off status above may still be sent; data already sent cannot be withdrawn from this computer.
en.ToolsTitle=Preparing media tools
en.ToolsSubtitle=Existing tools are verified and reused; missing ones are downloaded automatically.
en.ToolsChecking=Checking, downloading and verifying media tools. Please wait.
en.ToolsRetry=You can retry if the download fails; the existing installation is kept.
en.ToolsFailed=The media tools could not be prepared. Check your network and try again.

cht.StillRunning=Peach 仍在執行，未能自動結束。請從系統匣選單結束 Peach 後重試。
cht.TaskCheckFailed=無法確認背景工作狀態，安裝已取消。請等待工作結束後重試。
cht.MigrationFailed=本機資料庫未能更新到新版本，Peach 啟動後可能出錯。升級前的備份在資料目錄的 database 資料夾裡，檔名以 ledger.pre-migrate- 開頭。
cht.DataKept=Peach 已解除安裝。設定、本機資料庫和觀看紀錄保留在 %1，需要時可手動刪除；媒體檔案不受影響。
cht.DirectoryOverlapsData=程式目錄不能與 Peach 資料目錄重疊。請選擇獨立的程式資料夾。
cht.DirectoryNotDedicated=請選擇空資料夾或已有的 Peach 安裝目錄。解除安裝 Peach 時會移除整個程式資料夾。
cht.DirectoryNotWritable=目前使用者無法寫入程式目錄或其上層目錄。請選擇有寫入權限的位置，以便安裝和更新 Peach。
cht.DirectoryLink=程式目錄和資料目錄不能經過目錄連結。請選擇一般資料夾。
cht.DirectoryMove=請先解除安裝現有 Peach（保留資料），再選擇新的安裝目錄。
cht.ReportingFailed=版本統計與錯誤診斷選項未能儲存。首次設定或設定頁可再次選擇；未儲存的同意不會啟用上傳。
cht.LibrarySharingFailed=館藏與口味上傳選項未能儲存。可在設定頁重新選擇。
cht.TaskReporting=傳送版本統計與錯誤診斷（建議）：版本、系統資訊、隨機執行個體識別碼、故障類型、程式碼位置與發生次數
cht.TaskUploadGroup=資料上傳（可在設定頁關閉）：
cht.TaskLibrarySharing=上傳館藏與各類偏好明細（匿名化處理）
cht.RunStarRepo=開啟 Peach 儲存庫，為專案加星
cht.LibraryTitle=館藏與口味明細上傳
cht.LibrarySubtitle=用於 Peach 使用者群體的館藏結構與偏好研究。
cht.LibraryIntro=繼續表示同意以下明細與參與狀態的傳送範圍；不參與可返回取消勾選。
cht.LibraryText=作品：去除重複後的作品編號、評分、喜歡、不喜歡、已看、稍後看、播放次數、觀看比例與手動新增的受控內容標籤。自訂備註標籤保留在本機。%n%n偏好彙總：出演者、創作者、廠牌、系列、手動標籤、年代與時長分組的收藏、喜歡、不喜歡、觀看數量和評分分布（有編號作品與無編號項目分開），以及主動收藏的實體名稱。%n%n館藏涵蓋：檔案數量、有編號作品數量與無編號項目數量。無編號館藏只參與本機彙總。%n%n容量：近 7 天與 30 天實際觀測的容量天數、播放活躍天數與涵蓋天數，資料和快取的目前佔用、峰值、正增長量及快取清理量。清理量包含自動與手動快取清理，不含備份和日誌；未取得的值為空，不補足 30 天。播放活躍不代表全部日常使用。%n%n隨機研究識別碼：同意後為本執行個體隨機產生，用於關聯本次授權期間的館藏、容量及參與狀態。重新開啟時更換；不使用機器指紋或診斷識別碼。%n%n傳送週期：館藏、偏好和容量快照每週最多一次；啟用狀態每天最多一條聯絡日誌，並附目前週的快照編號、欄位版本、原始與壓縮位元組數、準備和投遞狀態。關閉時背景仍可實際嘗試一次僅含隨機研究識別碼、關閉狀態及必要版本和 UTC 時間的最小日誌，之後停發。%n%n版本與週期：Peach 版本、欄位版本、UTC 自然週。%n%n不上傳帳號、機器指紋、診斷識別碼、內部行號、檔名、路徑、標題、媒體、網址、搜尋詞及逐筆瀏覽或觀看紀錄。離線、解除安裝及傳送失敗不視為關閉，研究執行個體數不等於人數。%n%n完整明細可反映成人內容偏好；接收服務為獨立 Sentry 專案，可見連線 IP。%n%n可在設定頁檢視完整本機預覽或關閉。關閉後不再傳送研究明細，僅保留上述一次最小關閉狀態的傳送資格；已傳送資料無法透過本機開關撤回。
cht.ToolsTitle=準備媒體工具
cht.ToolsSubtitle=已有工具會驗證後重複使用，缺少時自動下載。
cht.ToolsChecking=正在檢查、下載並驗證媒體工具，請稍候。
cht.ToolsRetry=下載失敗可重試，現有安裝會保留。
cht.ToolsFailed=媒體工具未能準備完成，請檢查網路後重試。

chs.StillRunning=Peach 仍在运行，未能自动退出。请从托盘菜单退出 Peach 后重试。
chs.TaskCheckFailed=无法确认后台任务状态，安装已取消。请等待任务结束后重试。
chs.MigrationFailed=本地数据库未能更新到新版本，Peach 启动后可能出错。升级前的备份在数据目录的 database 文件夹里，文件名以 ledger.pre-migrate- 开头。
chs.DataKept=Peach 已卸载。设置、本地数据库和观看记录保留在 %1，需要时可手动删除；媒体文件不受影响。
chs.DirectoryOverlapsData=程序目录不能与 Peach 数据目录重叠。请选择独立的程序文件夹。
chs.DirectoryNotDedicated=请选择空文件夹或已有的 Peach 安装目录。卸载 Peach 时会移除整个程序文件夹。
chs.DirectoryNotWritable=当前用户无法写入程序目录或其上级目录。请选择有写入权限的位置，以便安装和更新 Peach。
chs.DirectoryLink=程序目录和数据目录不能经过目录链接。请选择普通文件夹。
chs.DirectoryMove=请先卸载现有 Peach（保留数据），再选择新的安装目录。
chs.ReportingFailed=版本统计与错误诊断选项未能保存。首次设置或设置页可再次选择；未保存的同意不会启用上传。
chs.LibrarySharingFailed=馆藏与口味上传选项未能保存。可在设置页重新选择。
chs.TaskReporting=发送版本统计与错误诊断（推荐）：版本、系统信息、随机实例标识、故障类型、代码位置与发生次数
chs.TaskUploadGroup=数据上传（可在设置页关闭）：
chs.TaskLibrarySharing=上传馆藏与各类偏好明细（匿名化处理）
chs.RunStarRepo=打开 Peach 仓库，给项目加星
chs.LibraryTitle=馆藏与口味明细上传
chs.LibrarySubtitle=用于 Peach 用户群体的馆藏结构与偏好研究。
chs.LibraryIntro=继续表示同意以下明细与参与状态的发送范围；不参与可返回取消勾选。
chs.LibraryText=作品：去重后的作品编号、评分、喜欢、不喜欢、已看、稍后看、播放次数、观看比例与手动添加的受控内容标签。自定义备注标签保留在本机。%n%n偏好汇总：出演者、创作者、厂牌、系列、手动标签、年代与时长分组的收藏、喜欢、不喜欢、观看数量和评分分布（有编号作品与无编号条目分开），以及主动收藏的实体名称。%n%n馆藏覆盖：文件数量、有编号作品数量与无编号条目数量。无编号馆藏只参与本机汇总。%n%n容量：近 7 天与 30 天实际观测的容量天数、播放活跃天数与覆盖天数，数据和缓存的当前占用、峰值、正增长量及缓存清理量。清理量包含自动与手动缓存清理，不含备份和日志；未取得的值为空，不补足 30 天。播放活跃不代表全部日常使用。%n%n随机研究标识：同意后为本实例随机生成，用于关联本次授权期间的馆藏、容量及参与状态。重新开启时更换；不使用机器指纹或诊断标识。%n%n发送周期：馆藏、偏好和容量快照每周最多一次；启用状态每天最多一条联系日志，并附当前周的快照编号、字段版本、原始与压缩字节数、准备和投递状态。关闭时后台仍可实际尝试一次仅含随机研究标识、关闭状态及必要版本和 UTC 时间的最小日志，之后停发。%n%n版本与周期：Peach 版本、字段版本、UTC 自然周。%n%n不上传账号、机器指纹、诊断标识、内部行号、文件名、路径、标题、媒体、网址、搜索词及逐条浏览或观看记录。离线、卸载及发送失败不视为关闭，研究实例数不等于人数。%n%n完整明细可反映成人内容偏好；接收服务为独立 Sentry 项目，可见连接 IP。%n%n可在设置页查看完整本机预览或关闭。关闭后不再发送研究明细，仅保留上述一次最小关闭状态的发送资格；已发送数据无法通过本机开关撤回。
chs.ToolsTitle=准备媒体工具
chs.ToolsSubtitle=已有工具会校验后复用，缺少时自动下载。
chs.ToolsChecking=正在检查、下载并校验媒体工具，请稍候。
chs.ToolsRetry=下载失败可重试，现有安装会保留。
chs.ToolsFailed=媒体工具未能准备完成，请检查网络后重试。

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "reporting"; Description: "{cm:TaskReporting}"; GroupDescription: "{cm:TaskUploadGroup}"
Name: "librarysharing"; Description: "{cm:TaskLibrarySharing}"; GroupDescription: "{cm:TaskUploadGroup}"; Flags: unchecked

[InstallDelete]
; PyInstaller 的依赖都在 _internal 里；覆盖安装留下上一版多出来的库会被新版误加载。
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#SourceDir}\*"; DestDir: "{tmp}\Peach-preflight"; Flags: dontcopy recursesubdirs createallsubdirs
#ifdef LiteInstaller
Source: "{tmp}\Peach-preflight\tools\*"; DestDir: "{app}\tools"; ExternalSize: 0; Flags: external ignoreversion recursesubdirs createallsubdirs
Source: "{tmp}\Peach-preflight\cloudflared.exe"; DestDir: "{app}"; ExternalSize: 0; Flags: external ignoreversion
Source: "{tmp}\Peach-preflight\cloudflared-manifest.json"; DestDir: "{app}"; ExternalSize: 0; Flags: external ignoreversion
#endif

[Icons]
Name: "{userprograms}\Peach"; Filename: "{app}\Peach.exe"; Parameters: "--show"
Name: "{userdesktop}\Peach"; Filename: "{app}\Peach.exe"; Parameters: "--show"; Tasks: desktopicon

[Run]
Filename: "{app}\Peach.exe"; Parameters: "--show"; Description: "{cm:LaunchProgram,Peach}"; Flags: nowait postinstall skipifsilent
Filename: "https://github.com/mosesmoon/peach_zhTW"; Description: "{cm:RunStarRepo}"; Flags: shellexec postinstall skipifsilent unchecked

[UninstallDelete]
; 自更新整目录换过之后，卸载记录里的文件清单不再完整，按目录整个移除。
Type: filesandordirs; Name: "{app}"

[Code]
var
  GuardPrepared: Boolean;
  LibrarySharingPage: TOutputMsgMemoWizardPage;
#ifdef LiteInstaller
  ToolsPrepared: Boolean;
  ToolsPage: TOutputMarqueeProgressWizardPage;
#endif

function GetCurrentProcessId(): LongWord;
  external 'GetCurrentProcessId@kernel32.dll stdcall';

{ 香港与新加坡的中文显示语言用英文安装界面：语言在启动时已经选定，只能带 /LANG=en 重开一次。
  静默安装没有界面，不重开；命令行已经指定 /LANG 时照它的。 }
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if ((GetUILanguage = $0C04) or (GetUILanguage = $1004)) and (ActiveLanguage <> 'en')
     and (not WizardSilent) and (Pos('/LANG=', Uppercase(GetCmdTail)) = 0) then
  begin
    if ShellExec('', ExpandConstant('{srcexe}'), GetCmdTail + ' /LANG=en', '', SW_SHOW, ewNoWait, ResultCode) then
      Result := False;
  end;
end;

procedure InitializeWizard();
begin
  LibrarySharingPage := CreateOutputMsgMemoPage(wpSelectTasks,
    CustomMessage('LibraryTitle'), CustomMessage('LibrarySubtitle'), CustomMessage('LibraryIntro'), '');
  LibrarySharingPage.RichEditViewer.Text := CustomMessage('LibraryText');
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := (PageID = LibrarySharingPage.ID) and not WizardIsTaskSelected('librarysharing');
end;

procedure FinishTaskGuard();
var
  ResultCode: Integer;
begin
  if GuardPrepared then
  begin
    if Exec(ExpandConstant('{tmp}\Peach-preflight\Peach.exe'),
      '--installer-finish "' + ExpandConstant('{app}') + '" ' + IntToStr(GetCurrentProcessId()),
      ExpandConstant('{tmp}\Peach-preflight'), SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0) then
      GuardPrepared := False;
  end;
end;

procedure DeinitializeSetup();
begin
  FinishTaskGuard();
end;

function DataRoot(): String;
begin
  Result := GetEnv('PEACH_DATA_ROOT');
  if Result = '' then
    Result := ExpandConstant('{localappdata}\Peach\peach-data');
end;

#include "directory-validation.iss"

function InstallationDirectoryError(): String;
var
  PreviousDirectory: String;
begin
  PreviousDirectory := '';
  RegQueryStringValue(HKCU,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{02D9748A-78F6-4866-AC75-918177194DAB}_is1',
    'Inno Setup: App Path', PreviousDirectory);
  Result := DirectoryError(WizardDirValue(), DataRoot(), PreviousDirectory);
  if Result = '' then
    Result := DirectoryError(WizardDirValue(), ExpandConstant('{localappdata}\Peach\peach-data'), PreviousDirectory);
  if Result <> '' then
    Result := CustomMessage(Result);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Error: String;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    Error := InstallationDirectoryError();
    Result := Error = '';
    if not Result then
      SuppressibleMsgBox(Error, mbError, MB_OK, IDOK);
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
  ErrorText: AnsiString;
begin
  Result := InstallationDirectoryError();
  if Result <> '' then
    Exit;
  if GuardPrepared then
    Exit;
  ExtractTemporaryFiles('{tmp}\Peach-preflight\*');
#ifdef LiteInstaller
  if not ToolsPrepared then
  begin
    if ToolsPage = nil then
      ToolsPage := CreateOutputMarqueeProgressPage(CustomMessage('ToolsTitle'), CustomMessage('ToolsSubtitle'));
    ToolsPage.SetText(CustomMessage('ToolsChecking'), CustomMessage('ToolsRetry'));
    ToolsPage.Show;
    ToolsPage.Animate;
    try
      ToolsPrepared := Exec(ExpandConstant('{tmp}\Peach-preflight\Peach.exe'),
        '--installer-tools "' + ExpandConstant('{app}') + '" "' + ExpandConstant('{src}\.') +
        '" "' + ExpandConstant('{tmp}\Peach-preflight\tools-error.txt') + '"',
        ExpandConstant('{tmp}\Peach-preflight'), SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
    finally
      ToolsPage.Hide;
    end;
    if not ToolsPrepared then
    begin
      Result := CustomMessage('ToolsFailed');
      if LoadStringFromFile(ExpandConstant('{tmp}\Peach-preflight\tools-error.txt'), ErrorText) then
        Result := UTF8Decode(ErrorText);
      Exit;
    end;
  end;
#endif
  if not Exec(ExpandConstant('{tmp}\Peach-preflight\Peach.exe'),
      '--installer-prepare "' + ExpandConstant('{app}') + '" ' + IntToStr(GetCurrentProcessId()) +
      ' "' + ExpandConstant('{tmp}\Peach-preflight\prepare-error.txt') + '"',
      ExpandConstant('{tmp}\Peach-preflight'), SW_HIDE, ewWaitUntilTerminated, ResultCode) or
      (ResultCode <> 0) then
  begin
    Result := CustomMessage('TaskCheckFailed');
    if LoadStringFromFile(ExpandConstant('{tmp}\Peach-preflight\prepare-error.txt'), ErrorText) then
      Result := UTF8Decode(ErrorText);
  end
  else
    GuardPrepared := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  ReportingConsent: String;
  LibraryConsent: String;
begin
  if (CurStep = ssPostInstall) and not WizardSilent() then
  begin
    ReportingConsent := '0';
    if WizardIsTaskSelected('reporting') then ReportingConsent := '1';
    if not Exec(ExpandConstant('{app}\Peach.exe'),
      '--installer-reporting ' + ReportingConsent + ' ' + ReportingConsent,
      ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
      SuppressibleMsgBox(CustomMessage('ReportingFailed'), mbError, MB_OK, IDOK);
    LibraryConsent := '0';
    if WizardIsTaskSelected('librarysharing') then LibraryConsent := '1';
    if not Exec(ExpandConstant('{app}\Peach.exe'),
      '--installer-library-sharing ' + LibraryConsent,
      ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
      SuppressibleMsgBox(CustomMessage('LibrarySharingFailed'), mbError, MB_OK, IDOK);
  end;
  { 服务启动时不迁移账本；覆盖安装换了程序，要在这里补上。没有账本的新机器不跑，
    否则会凭空建出账本，首次设置页就再也不出现。migrate 自己会先备份。 }
  if CurStep = ssPostInstall then
    if not Exec(ExpandConstant('{tmp}\Peach-preflight\Peach.exe'),
                '--installer-migrate "' + ExpandConstant('{app}') + '"', ExpandConstant('{tmp}\Peach-preflight'),
                SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
      SuppressibleMsgBox(CustomMessage('MigrationFailed'), mbError, MB_OK, IDOK);
  if CurStep = ssPostInstall then
    FinishTaskGuard();
end;

function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if Exec(ExpandConstant('{app}\Peach.exe'), '--installer-uninstall', ExpandConstant('{app}'),
          SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 1) then
  begin
    SuppressibleMsgBox(CustomMessage('StillRunning'), mbError, MB_OK, IDOK);
    Result := False;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and DirExists(DataRoot()) then
    SuppressibleMsgBox(FmtMessage(CustomMessage('DataKept'), [DataRoot()]), mbInformation, MB_OK, IDOK);
end;
