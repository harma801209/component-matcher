"""User-initiated image paste through the existing Streamlit BOM uploader."""


def build_bom_image_clipboard_html():
    return r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>
body{margin:0;font:14px "Microsoft YaHei","Segoe UI",sans-serif;color:#45658f}
button{border:1px solid #b8cbeb;background:#f6f9ff;border-radius:8px;padding:8px 14px;color:#1755e8;cursor:pointer;font:inherit}
button:focus-visible{outline:2px solid #1755e8;outline-offset:2px}
#paste-status{margin-left:12px;font-size:13px}
</style></head><body>
<button id="paste-area" type="button" aria-label="粘贴截图区域">点击这里，再按 Ctrl+V 粘贴截图</button>
<span id="paste-status" role="status" aria-live="polite"></span>
<script>
(() => {
  const localDocument = document;
  const button = localDocument.getElementById('paste-area');
  const status = localDocument.getElementById('paste-status');
  const say = message => { status.textContent = message; };
  let host;
  try { host = window.parent; void host.document.body; }
  catch (_) { say('当前浏览器不支持粘贴，请使用上传或拖拽。'); return; }
  const key = '__bomImagePasteController';
  const previous = host[key];
  if (previous) previous.dispose();
  const extensions = {'image/png':'png','image/jpeg':'jpg','image/webp':'webp',
                      'image/bmp':'bmp','image/tiff':'tiff'};
  function uploader() {
    return Array.from(host.document.querySelectorAll('[data-testid="stFileUploader"]'))
      .find(node => node.textContent.includes('上传 BOM Excel/CSV/图片'))
      ?.querySelector('input[type="file"]');
  }
  function paste(event) {
    const data = event.clipboardData;
    if (!data) return;
    let files = Array.from(data.items || []).filter(item => item.kind === 'file' && item.type.startsWith('image/'))
      .map(item => item.getAsFile()).filter(Boolean);
    if (!files.length) files = Array.from(data.files || []).filter(file => file.type.startsWith('image/'));
    // Text/Excel cell paste is not an image upload and must behave normally.
    if (!files.length) return;
    const target = event.target;
    if (target?.closest?.('input:not([type="file"]),textarea,[contenteditable="true"]')) return;
    const input = uploader();
    if (!input || input.disabled) return;
    event.preventDefault();
    if (files.length !== 1) { say('请一次粘贴一张图片。'); return; }
    const image = files[0];
    const extension = extensions[image.type];
    if (!extension) { say('此图片格式不支持粘贴，请使用 PNG/JPG 截图。'); return; }
    if (!image.size || image.size > 100 * 1024 * 1024) { say('图片为空或超过100MB，请重新截图。'); return; }
    try {
      const transfer = new host.DataTransfer();
      transfer.items.add(new host.File([image], `粘贴截图-${Date.now()}.${extension}`, {type:image.type}));
      input.files = transfer.files;
      input.dispatchEvent(new host.Event('change', {bubbles:true}));
      say('图片已交给上传入口，请稍候；不会自动开始匹配。');
    } catch (_) { say('粘贴未成功，请使用上传或拖拽。'); }
  }
  button.addEventListener('click', () => { button.focus(); say('请按 Ctrl+V（Mac：⌘V）。'); });
  localDocument.addEventListener('paste', paste);
  host.document.addEventListener('paste', paste);
  const controller = {
    dispose() {
      host.document.removeEventListener('paste', paste);
      localDocument.removeEventListener('paste', paste);
      if (host[key] === controller) delete host[key];
    }
  };
  host[key] = controller;
  window.addEventListener('pagehide', () => controller.dispose(), {once:true});
})();
</script></body></html>'''
