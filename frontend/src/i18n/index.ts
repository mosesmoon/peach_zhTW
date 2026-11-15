/* 界面文案的翻译入口（ADR-0156）。
 *
 * 源文是仓库根下的 `resources/locales/zh-CN/<命名空间>.json`，英文在 `resources/locales/en/`，两份由同一个 PR 维护；其他语言经 Weblate 回流。
 * 界面语言在模块求值时从本地偏好同步算出（默认「自动」：浏览器语言优先，其次系统语言），整页只有这一份实例：
 * 导航词表这类模块在顶层就取译文，换语言靠整页重载，不做运行中切换。缺译文的键回落到 zh-CN。 */
import i18next from 'i18next';

import { SETTINGS_KEY } from '../settings-key';
import enCatalog from '../../../resources/locales/en/catalog.json' with { type: 'json' };
import enCleanup from '../../../resources/locales/en/cleanup.json' with { type: 'json' };
import enFollow from '../../../resources/locales/en/follow.json' with { type: 'json' };
import enManage from '../../../resources/locales/en/manage.json' with { type: 'json' };
import enNavigation from '../../../resources/locales/en/navigation.json' with { type: 'json' };
import enOnboarding from '../../../resources/locales/en/onboarding.json' with { type: 'json' };
import enSettings from '../../../resources/locales/en/settings.json' with { type: 'json' };
import enServer from '../../../resources/locales/en/server.json' with { type: 'json' };
import enShell from '../../../resources/locales/en/shell.json' with { type: 'json' };
import zhCatalog from '../../../resources/locales/zh-CN/catalog.json' with { type: 'json' };
import zhCleanup from '../../../resources/locales/zh-CN/cleanup.json' with { type: 'json' };
import zhFollow from '../../../resources/locales/zh-CN/follow.json' with { type: 'json' };
import zhManage from '../../../resources/locales/zh-CN/manage.json' with { type: 'json' };
import zhNavigation from '../../../resources/locales/zh-CN/navigation.json' with { type: 'json' };
import zhOnboarding from '../../../resources/locales/zh-CN/onboarding.json' with { type: 'json' };
import zhSettings from '../../../resources/locales/zh-CN/settings.json' with { type: 'json' };
import zhServer from '../../../resources/locales/zh-CN/server.json' with { type: 'json' };
import zhShell from '../../../resources/locales/zh-CN/shell.json' with { type: 'json' };
import twCatalog from '../../../resources/locales/zh-TW/catalog.json' with { type: 'json' };
import twCleanup from '../../../resources/locales/zh-TW/cleanup.json' with { type: 'json' };
import twFollow from '../../../resources/locales/zh-TW/follow.json' with { type: 'json' };
import twManage from '../../../resources/locales/zh-TW/manage.json' with { type: 'json' };
import twNavigation from '../../../resources/locales/zh-TW/navigation.json' with { type: 'json' };
import twOnboarding from '../../../resources/locales/zh-TW/onboarding.json' with { type: 'json' };
import twSettings from '../../../resources/locales/zh-TW/settings.json' with { type: 'json' };
import twServer from '../../../resources/locales/zh-TW/server.json' with { type: 'json' };
import twShell from '../../../resources/locales/zh-TW/shell.json' with { type: 'json' };

export const INTERFACE_LANGUAGES = ['zh-CN', 'zh-TW', 'en'] as const;
export type InterfaceLanguage = typeof INTERFACE_LANGUAGES[number];
export const SOURCE_LANGUAGE: InterfaceLanguage = 'zh-CN';

export const resources = {
  'zh-CN': { navigation: zhNavigation, shell: zhShell, settings: zhSettings, cleanup: zhCleanup, manage: zhManage, follow: zhFollow, catalog: zhCatalog, onboarding: zhOnboarding, server: zhServer },
  'zh-TW': { navigation: twNavigation, shell: twShell, settings: twSettings, cleanup: twCleanup, manage: twManage, follow: twFollow, catalog: twCatalog, onboarding: twOnboarding, server: twServer },
  en: { navigation: enNavigation, shell: enShell, settings: enSettings, cleanup: enCleanup, manage: enManage, follow: enFollow, catalog: enCatalog, onboarding: enOnboarding, server: enServer },
} as const;

/** 设置里能选的值：`auto` 按浏览器与系统语言自动选，其余是固定的界面语言。 */
export const INTERFACE_LANGUAGE_CHOICES = ['auto', ...INTERFACE_LANGUAGES] as const;
export type InterfaceLanguageChoice = typeof INTERFACE_LANGUAGE_CHOICES[number];
/** 都对不上时用英文：既读不懂中文、也没有自己语言译文的人，英文比中文更可能读得懂。 */
const UNMATCHED_LANGUAGE: InterfaceLanguage = 'en';

export const isInterfaceLanguage = (value: unknown): value is InterfaceLanguage =>
  INTERFACE_LANGUAGES.includes(value as InterfaceLanguage);
export const isInterfaceLanguageChoice = (value: unknown): value is InterfaceLanguageChoice =>
  INTERFACE_LANGUAGE_CHOICES.includes(value as InterfaceLanguageChoice);

/** 一个语言标签对应哪种界面语言（ADR-0201）。
 *  先去掉 `.编码`、`@修饰`，`_` 当 `-`，不分大小写。主语言不是 zh 的只认 en。
 *  中文里文字子标签优先于地区：含 Hant 给繁体、含 Hans 给简体；都没有时 TW、HK、MO 给繁体，其余（含只写 zh）给简体。
 *  与后端 `system_language.interface_language` 逐项一致，两边的测试用同一组案例。 */
export function matchInterfaceLanguage(tag: unknown): InterfaceLanguage | null {
  const parts = typeof tag === 'string' ? tag.trim().toLowerCase().split(/[.@]/)[0]!.replace(/_/g, '-').split('-') : [];
  if (parts[0] === 'en') return 'en';
  if (parts[0] !== 'zh') return null;
  const subtags = parts.slice(1);
  if (subtags.includes('hant')) return 'zh-TW';
  if (subtags.includes('hans')) return 'zh-CN';
  return subtags.some((subtag) => ['tw', 'hk', 'mo'].includes(subtag)) ? 'zh-TW' : 'zh-CN';
}

/** 浏览器给出的语言，按用户的偏好顺序；最后是 Intl 的默认区域，它跟着浏览器界面或系统区域走。 */
export function browserLanguages(): string[] {
  const nav = globalThis.navigator;
  let intl = '';
  try { intl = Intl.DateTimeFormat().resolvedOptions().locale } catch { /* 没有 Intl 就不看它 */ }
  return [...(nav?.languages ?? []), nav?.language ?? '', intl].filter(Boolean);
}

/** 选「自动」时实际用哪种：先按浏览器语言的顺序找第一个有译文的，再看运行 Peach 的电脑的系统语言，都没有就用英文。 */
export function resolveInterfaceLanguage(choice: unknown, systemLanguage: unknown, browser: readonly string[] = browserLanguages()): InterfaceLanguage {
  if (isInterfaceLanguage(choice)) return choice;
  for (const tag of browser) {
    const match = matchInterfaceLanguage(tag);
    if (match) return match;
  }
  return matchInterfaceLanguage(systemLanguage) ?? UNMATCHED_LANGUAGE;
}

/** 本地偏好里存的选择与系统语言算出来的界面语言；没存或存坏时按「自动」算。 */
export function storedInterfaceLanguage(
  storage: Pick<Storage, 'getItem'> | undefined = globalThis.localStorage, browser: readonly string[] = browserLanguages(),
): InterfaceLanguage {
  let saved: { interfaceLanguage?: unknown; systemLanguage?: unknown } = {};
  try { saved = JSON.parse(storage?.getItem(SETTINGS_KEY) || '{}') ?? {} } catch { /* 坏掉的存量按自动算 */ }
  return resolveInterfaceLanguage(saved.interfaceLanguage, saved.systemLanguage, browser);
}

/** 按给定语言建一份同步就绪的实例；页面用模块级那一份，测试用它比对各语言。 */
export function createTranslator(language: InterfaceLanguage) {
  const instance = i18next.createInstance();
  void instance.init({
    lng: language, fallbackLng: SOURCE_LANGUAGE, supportedLngs: [...INTERFACE_LANGUAGES],
    resources, ns: Object.keys(resources[SOURCE_LANGUAGE]), defaultNS: 'navigation',
    // 中文的句间分隔是空串（英文是空格），空串要原样返回，不能当成缺键。
    initAsync: false, returnNull: false, returnEmptyString: true, interpolation: { escapeValue: false },
  });
  return instance;
}

export const interfaceLanguage = storedInterfaceLanguage();
const translator = createTranslator(interfaceLanguage);
/** 中文名字排序用的区域：繁体界面按 zh-TW（笔画序），其余界面沿用 zh-CN（拼音序）。 */
export const collationLocale = interfaceLanguage === 'zh-TW' ? 'zh-TW' : 'zh-CN';
if (typeof document !== 'undefined') document.documentElement.lang = interfaceLanguage;
/** 繁体中文界面的内嵌字体（台湾圆体子集）样式表。只在繁体界面引入，别的语言不下载这份 `@font-face` 清单；
 *  服务端直接出的页面由 `peach.web_entry.page_shell` 按同一路径引入。 */
export const TRADITIONAL_FONT_STYLESHEET = '/vendor/taiwan-pearl/2.125/index.css';
if (typeof document !== 'undefined' && interfaceLanguage === 'zh-TW'
  && !document.querySelector(`link[href="${TRADITIONAL_FONT_STYLESHEET}"]`)) {
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = TRADITIONAL_FONT_STYLESHEET;
  document.head.append(link);
}

/** 取当前界面语言的译文，键写成 `命名空间:路径`。 */
export const t = translator.t.bind(translator);
/** 这条键有没有译文（含回落到 zh-CN）。缺键时 `t()` 返回键名，判断有没有译文只能用它。 */
export const hasTranslation = (key: string): boolean => translator.exists(key);

/** 外壳页面 `web/index.html` 里写死的源文：元素用 `data-i18n`（文字）和 `data-i18n-title`、`data-i18n-aria-label`、
 *  `data-i18n-placeholder`（属性）标出键，这里按界面语言换上。源语言不用换。 */
export function localizeDocument(root: ParentNode): void {
  root.querySelectorAll<HTMLElement>('[data-i18n]').forEach((node) => { node.textContent = t(node.dataset.i18n!); });
  for (const [attribute, data] of [['title', 'i18nTitle'], ['aria-label', 'i18nAriaLabel'], ['placeholder', 'i18nPlaceholder']] as const) {
    root.querySelectorAll<HTMLElement>(`[data-i18n-${attribute}]`).forEach((node) => node.setAttribute(attribute, t(node.dataset[data]!)));
  }
}
if (typeof document !== 'undefined' && interfaceLanguage !== SOURCE_LANGUAGE) localizeDocument(document);

/** 把几项连成一句里的列表：中文用顿号，英文用逗号。 */
export const joinList = (items: readonly string[]): string => items.join(t('shell:format.listSeparator'));
/** 句中引用一个名字：中文用直角引号，英文用弯引号。 */
export const quoted = (text: string): string => t('shell:format.quoted', { text });
