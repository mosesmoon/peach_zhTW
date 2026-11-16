/** 语言写法只用于标签。查询、路由和写入始终使用调用方持有的原始名称与 ID。 */
export type NameLanguage = 'zh-CN' | 'zh-TW' | 'ja';
export interface NameWriting {
  id: number; kind: string; canonical_name: string; zh_cn: string | null; ja: string | null;
  /** JavDB 现名的繁体写法；没有时繁体中文显示日文。 */
  zh_tw?: string | null;
}
const names = new Map<string, NameWriting>();
const identities = new Map<string, NameWriting>();
const spellings = new Map<string, Map<number, NameWriting>>();
let glyphs: Record<string, string> = {};
const listeners = new Set<() => void>();
let language: NameLanguage = 'zh-CN';
let revision = 0;
const notify = () => { revision++; listeners.forEach(listener => listener()) };
export const nameRevision = () => revision;
export const subscribeNames = (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener) } };
export const nameLanguage = () => language;
export function setNameLanguage(value: NameLanguage): void {
  if (language === value) return;
  language = value;
  notify();
}
export function registerNameWritings(rows: NameWriting[], sharedGlyphs: Record<string, string> = {}): void {
  names.clear(); identities.clear(); spellings.clear();
  glyphs = sharedGlyphs;
  for (const row of rows) indexNameWriting(row);
  notify();
}
function indexNameWriting(row: NameWriting): void {
  identities.set(`${row.kind}/${row.id}`, row);
  names.set(`${row.kind}/${row.canonical_name}`, row);
  for (const name of [row.zh_cn, row.ja, row.zh_tw]) {
    if (!name) continue;
    const key = `${row.kind}/${name}`;
    const candidates = spellings.get(key) || new Map<number, NameWriting>();
    candidates.set(row.id, row);
    spellings.set(key, candidates);
  }
}
export function registerNameWriting(row: NameWriting): void {
  indexNameWriting(row);
  notify();
}
export function entityWriting(kind: string, name: string, id?: number | null): NameWriting | undefined {
  const byId = id ? identities.get(`${kind}/${id}`) : undefined;
  if (byId && [byId.canonical_name, byId.zh_cn, byId.ja, byId.zh_tw].includes(name)) return byId;
  const key = `${kind}/${name}`;
  const canonical = names.get(key);
  if (canonical) return canonical;
  const candidates = spellings.get(key);
  return id ? candidates?.get(id) : candidates?.size === 1 ? candidates.values().next().value : undefined;
}
export function entityDisplayName(kind: string, name: string, id?: number | null): string {
  const row = entityWriting(kind, name, id);
  if (language === 'ja') return row?.ja || name;
  /* 繁体中文：有 JavDB 的繁体写法就用，没有用日文；不把简体名逐字硬转。 */
  if (language === 'zh-TW') return row?.zh_tw || row?.ja || name;
  if (row?.zh_cn) return row.zh_cn;
  if ((kind !== 'performer' && kind !== 'creator') || !/^[\p{Script=Han}々\s]+$/u.test(name)) return name;
  const written: string[] = [];
  // i18n-exempt: 日文人名里的叠字符号，是名字内容
  for (const char of name) written.push(char === '々' ? written.at(-1) || char : glyphs[char] || char);
  return written.join('');
}
