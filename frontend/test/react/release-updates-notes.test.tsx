/* 检查更新里的更新说明按界面语言取份：正体界面取繁體中文段，缺它时回落简体段；其余中文取简体，非中文取英文。 */
import { afterEach, describe, expect, it, vi } from 'vitest';

import type { ReleaseNotes, ReleaseNotesPart } from '../../src/react/bundle';
import { SETTINGS_KEY } from '../../src/settings-key';
import { mountRoot } from './render';

const part = (title: string, text: string): ReleaseNotesPart => ({
  lead: [], groups: [{ title, items: [{ area: '', text }] }],
});
const en = part('Added', 'English note');
const simplified = part('新增', '简体说明');
const traditional = part('新增', '正體說明');
const row = (withTraditional: boolean): ReleaseNotes => ({
  version: '0.9.0', url: 'https://example.test/releases/tag/v0.9.0', en, 'zh-CN': simplified,
  ...(withTraditional ? { 'zh-TW': traditional } : {}),
});

async function load(language: string) {
  vi.resetModules();
  // 正体界面会往 head 里挂字体样式表，测试环境不加载外部样式。
  vi.spyOn(document.head, 'append').mockImplementation(() => undefined);
  localStorage.setItem(SETTINGS_KEY, JSON.stringify({ interfaceLanguage: language }));
  return import('../../src/react/settings/release-updates');
}

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.removeItem(SETTINGS_KEY);
  vi.resetModules();
});

describe('更新说明的语言选择', () => {
  it('正体界面取繁體中文段，没有这一段时回落到简体段', async () => {
    const { releaseNotesPart } = await load('zh-TW');
    expect(releaseNotesPart(row(true), 'zh-TW')).toBe(traditional);
    expect(releaseNotesPart(row(false), 'zh-TW')).toBe(simplified);
  });

  it('简体界面取简体段，非中文界面取英文正文', async () => {
    const { releaseNotesPart } = await load('zh-CN');
    expect(releaseNotesPart(row(true), 'zh-CN')).toBe(simplified);
    expect(releaseNotesPart(row(true), 'zh')).toBe(simplified);
    expect(releaseNotesPart(row(true), 'en')).toBe(en);
  });

  it('正体界面展开后显示的是繁體中文段，旧结果没有这一段时显示简体段', async () => {
    const { ReleaseChangelog } = await load('zh-TW');
    const { host } = await mountRoot(<ReleaseChangelog notes={[row(true)]} />);
    expect(host.textContent).toContain('正體說明');
    expect(host.textContent).not.toContain('简体说明');
    const { host: fallback } = await mountRoot(<ReleaseChangelog notes={[row(false)]} />);
    expect(fallback.textContent).toContain('简体说明');
  });
});
