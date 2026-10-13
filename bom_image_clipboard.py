"""Unified click, drag/drop and user-initiated file/image paste in the BOM uploader."""


def build_bom_image_clipboard_html():
    return r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"></head><body>
<script>
(() => {
  let host;
  try { host = window.parent; void host.document.body; } catch (_) { return; }
  const key = '__bomImagePasteController';
  const previous = host[key];
  if (previous) previous.dispose();
  let disposed = false, zoneState = null, buttonState = null, message = '';
  const allowed = new Set(['xlsx','xls','csv','png','jpg','jpeg','webp','bmp','tif','tiff']);
  const mimeExtensions = {'image/png':'png','image/jpeg':'jpg','image/webp':'webp',
    'image/bmp':'bmp','image/tiff':'tiff','text/csv':'csv','application/csv':'csv',
    'application/vnd.ms-excel':'xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':'xlsx'};
  const documents = [host.document];
  try { if (host.parent !== host && host.parent.document !== host.document) documents.push(host.parent.document); } catch (_) {}
  const style = host.document.createElement('style');
  style.dataset.bomUploadStyle = 'true';
  style.textContent = `
    [data-bom-upload-zone]{display:flex!important;flex-direction:row!important;flex-wrap:wrap;align-items:center!important;gap:12px;
      cursor:pointer;padding:16px!important;min-height:90px;box-sizing:border-box}
    [data-bom-upload-zone]:focus-visible{outline:2px solid #1755e8;outline-offset:2px}
    [data-bom-upload-zone] [data-testid="stFileUploaderDropzoneInstructions"]{display:none!important}
    [data-bom-upload-zone] button[data-bom-upload-button]>*:not(svg){display:none!important}
    [data-bom-upload-zone] button[data-bom-upload-button]{font-size:0!important;flex-shrink:0;
      width:auto!important;min-width:138px!important;min-height:40px!important;height:auto!important;
      padding:8px 12px!important;border:1px solid #c7d5e7!important;border-radius:8px!important;
      background:#fff!important;color:#18395f!important;display:inline-flex!important;
      align-items:center!important;justify-content:center!important;gap:6px!important}
    [data-bom-upload-zone] button[data-bom-upload-button]::after{content:"上传文件或图片";
      font:inherit;font-size:14px;line-height:1.4}
    [data-bom-upload-hint]{flex:1 1 260px;min-width:0;color:#45658f;font-size:14px;line-height:1.7}
    [data-bom-upload-hint] small{display:block;color:#7185a5;font-size:12px}
    [data-bom-paste-status]{display:block;color:#1755e8;font-size:13px;line-height:1.5}
    [data-bom-paste-status]:empty{display:none}
    @media(max-width:600px){[data-bom-upload-zone]{padding:12px!important;gap:8px}}
  `;
  host.document.head.appendChild(style);
  function widget() {
    return Array.from(host.document.querySelectorAll('[data-testid="stFileUploader"]'))
      .find(node => node.textContent.includes('上传 BOM Excel/CSV/图片'));
  }
  function input() { return widget()?.querySelector('input[type="file"]'); }
  function restoreAttribute(node,name,value) {
    if (value === null) node.removeAttribute(name); else node.setAttribute(name,value);
  }
  function detachButton() {
    if (!buttonState) return;
    const {button,label} = buttonState;
    button.removeAttribute('data-bom-upload-button');
    if (button.getAttribute('aria-label') === '上传文件或图片') restoreAttribute(button,'aria-label',label);
    buttonState = null;
  }
  function detachZone() {
    detachButton();
    if (!zoneState) return;
    const {zone,hint,tabindex,label,role} = zoneState;
    zone.removeEventListener('click',openPicker,true);
    zone.removeEventListener('keydown',openPickerKey,true);
    zone.removeEventListener('drop',clearStatus,true);
    zone.removeAttribute('data-bom-upload-zone');
    restoreAttribute(zone,'tabindex',tabindex);
    restoreAttribute(zone,'aria-label',label);
    restoreAttribute(zone,'role',role);
    hint.remove();
    zoneState = null;
  }
  function openPicker(event) {
    if (event.target?.closest?.('button,input,a')) return;
    const fileInput = input();
    if (!fileInput || fileInput.disabled) return;
    event.preventDefault();
    event.stopPropagation();
    fileInput.click();
  }
  function openPickerKey(event) {
    if (event.target !== zoneState?.zone || !['Enter',' '].includes(event.key)) return;
    openPicker(event);
  }
  function attach() {
    if (disposed) return;
    const zone = widget()?.querySelector('[data-testid="stFileUploaderDropzone"]');
    if (zone !== zoneState?.zone) detachZone();
    if (!zone) return;
    if (!zoneState) {
      const hint = host.document.createElement('div');
      hint.dataset.bomUploadHint = 'true';
      const text = host.document.createElement('div');
      text.textContent = '点击或拖拽上传，也可直接在页面按 Ctrl+V 粘贴';
      const formats = host.document.createElement('small');
      formats.textContent = '支持 Excel、CSV 和图片 · 单个文件最多 100MB · Mac：⌘V';
      const status = host.document.createElement('span');
      status.dataset.bomPasteStatus = 'true';
      status.setAttribute('role','status');
      status.setAttribute('aria-live','polite');
      status.textContent = message;
      hint.append(text,formats,status);
      zoneState = {zone,hint,status,tabindex:zone.getAttribute('tabindex'),
        label:zone.getAttribute('aria-label'),role:zone.getAttribute('role')};
      zone.dataset.bomUploadZone = 'true';
      zone.tabIndex = 0;
      zone.setAttribute('role','region');
      zone.setAttribute('aria-label','上传区：点击、拖拽或 Ctrl+V 粘贴文件和图片');
      zone.appendChild(hint);
      zone.addEventListener('click',openPicker,true);
      zone.addEventListener('keydown',openPickerKey,true);
      zone.addEventListener('drop',clearStatus,true);
    }
    // New Streamlit puts file-removal controls before its "Add files" button.
    // Never relabel/restyle a file chip's delete button as the upload action.
    const button = Array.from(zone.querySelectorAll('button')).find(candidate =>
      !candidate.closest('[data-testid="stFileChip"],[data-testid="stFileChipDeleteBtn"],[data-testid="stFileUploaderFile"]'));
    if (button !== buttonState?.button) {
      detachButton();
      if (button) {
        buttonState = {button,label:button.getAttribute('aria-label')};
        button.dataset.bomUploadButton = 'true';
        button.setAttribute('aria-label','上传文件或图片');
      }
    }
  }
  function say(value) {
    message = value;
    attach();
    if (zoneState && zoneState.status.textContent !== value) zoneState.status.textContent = value;
  }
  function clearStatus(event) {
    if (event.type === 'drop' || event.target === input()) say('');
  }
  function paste(event) {
    const data = event.clipboardData;
    if (!data || disposed) return;
    // Leave normal cell/field paste alone, including mixed Excel text+image data.
    if (event.target?.closest?.('input:not([type="file"]),textarea,[contenteditable="true"],[data-testid="stDataFrame"],[data-testid="stForm"]')) return;
    const fileInput = input();
    if (!fileInput || fileInput.disabled) return;
    let files = Array.from(data.items || []).filter(item => item.kind === 'file')
      .map(item => item.getAsFile()).filter(Boolean);
    if (!files.length) files = Array.from(data.files || []);
    if (!files.length) {
      const types = Array.from(data.types || []);
      const text = data.getData?.('text/plain') || '';
      if (types.includes('Files') || /^(?:[a-z]:[\\/]|file:\/\/)[^\r\n]+\.(?:xlsx|xls|csv|png|jpe?g|webp|bmp|tiff?)\s*$/i.test(text.trim())) {
        say('浏览器没有提供文件内容，请点击上传或拖拽文件。');
      }
      return;
    }
    event.preventDefault();
    if (files.length !== 1) { say('请一次粘贴一个文件或一张图片。'); return; }
    const file = files[0];
    const originalName = String(file.name || '').split(/[\\/]/).pop().slice(0,200);
    const namedExtension = originalName.match(/\.([^.]+)$/)?.[1]?.toLowerCase();
    const extension = namedExtension || mimeExtensions[file.type];
    if (!allowed.has(extension)) { say('请上传 Excel、CSV 或 PNG/JPG 等支持的图片。'); return; }
    if (!file.size || file.size > 100 * 1024 * 1024) { say('文件为空或超过100MB，请重新选择。'); return; }
    const genericImage = /^image\.(?:png|jpe?g|webp|bmp|tiff?)$/i.test(originalName);
    const name = (!originalName || !namedExtension || genericImage)
      ? `${file.type.startsWith('image/') ? '粘贴截图' : '粘贴文件'}-${Date.now()}.${extension}` : originalName;
    try {
      const transfer = new host.DataTransfer();
      transfer.items.add(new host.File([file], name, {type:file.type,lastModified:file.lastModified}));
      fileInput.files = transfer.files;
      fileInput.dispatchEvent(new host.Event('change', {bubbles:true}));
      say('已接收粘贴内容，正在读取；不会自动开始匹配。');
    } catch (_) { say('粘贴未成功，请点击上传或拖拽文件。'); }
  }
  const observer = new host.MutationObserver(attach);
  observer.observe(host.document.body,{childList:true,subtree:true});
  for (const doc of documents) doc.addEventListener('paste',paste);
  host.document.addEventListener('change',clearStatus,true);
  const controller = {
    dispose() {
      if (disposed) return;
      disposed = true;
      observer.disconnect();
      for (const doc of documents) doc.removeEventListener('paste',paste);
      host.document.removeEventListener('change',clearStatus,true);
      detachZone();
      style.remove();
      if (host[key] === controller) delete host[key];
    }
  };
  host[key] = controller;
  attach();
  const frame = window.frameElement;
  const container = frame?.closest?.('[data-testid="stElementContainer"],.element-container');
  if (container) container.style.display = 'none';
  window.addEventListener('pagehide', () => controller.dispose(), {once:true});
})();
</script></body></html>'''
