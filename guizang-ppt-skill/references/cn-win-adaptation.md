# 中文/Windows 环境适配要点

本文件记录在中文 Windows 环境下使用 guizang-ppt-skill 生成网页 PPT 时踩过的坑和最佳实践。

## 1. 字体加载

**问题**：Google Fonts CDN（fonts.googleapis.com）在中国大陆被墙，导致衬线/无衬线字体无法加载，页面回退到系统默认字体，中文排版完全变形。

**解决**：
- 删除 `<link>` 中的 Google Fonts 引用
- 改用系统字体回退栈：
  ```css
  --serif-zh:"Noto Serif SC","Source Han Serif SC","思源宋体",serif;
  --sans-zh:"Noto Sans SC","Source Han Sans SC","微软雅黑","Microsoft YaHei",sans-serif;
  ```
- 或在 `<style>` 中用 `@import` 从 jsDelivr（有国内CDN节点）加载
- 不依赖任何外网字体 CDN，确保断网/墙内均可用

## 2. 中文排版字号

**问题**：skILL.md 中预设的 `10vw`（h-hero）、`6.2vw`（h-xl）等字号对中文方块字过大，在 1920×1080 屏上会溢出容器宽度。

**规律**：中文单字宽度 ≈ 英文 2 倍。同样 8 个中文字符需要英文 16 字符的宽度。

**解决**：所有字号改用 `min(Xvw, Yvh)` 双约束：
```css
.h-hero{font-size:min(7vw,8vh)}       /* 中文长标题用 */
.h-xl{font-size:min(5vw,6.5vh)}       /* 章节标题 */
.h-md{font-size:min(1.8vw,2.4vh)}     /* 卡片标题 */
.body-zh{font-size:min(1.05vw,1.6vh)} /* 正文 */
```

**中文大标题字号分档参考**：

| 标题形态 | 推荐字号 |
|---|---|
| 1 行，≤ 6 个中文字符 | `min(7vw, 8vh)` |
| 1 行，7-10 个中文字符 | `min(5.5vw, 7vh)` |
| 2 行，每行 ≤ 6 个字符 | `min(6vw, 7.5vh)` |
| 2 行，每行 7-10 个字符 | `min(5vw, 6.5vh)` |

## 3. JS 变量名冲突

**问题**：template.html 的 WebGL 初始化部分用 `let dk` 作为暗色背景绘制函数变量名，而翻页导航部分又用 `const dk` 作为 deck 容器元素变量名。浏览器报 `Identifier 'dk' has already been declared`，整个脚本不执行，翻页/键盘/ESC索引全部失效。

**解决**：翻页导航变量改为 `deckEl`，与 WebGL 的 `dk` 隔离。

```javascript
const deckEl = document.getElementById('deck');  // ✅ 不冲突
// 不要用 const dk = document.getElementById('deck');  // ❌ 与 let dk 冲突
```

**排查方法**：翻页不工作时打开浏览器 F12 → Console，看是否有 `Identifier already declared` 报错。

## 4. 音频配音集成

**需求**：翻页时自动播放对应页的配音，切换到下一页时停止上一页音频。

**实现**：
```html
<!-- 在 <div id="deck"> 开头插入 audio 元素 -->
<audio id="audio-01" preload="auto" src="audio/slide-01.mp3"></audio>
<!-- ... 每页一个，id 按页码补零 -->

<!-- 在 go() 函数中切换音频 -->
function go(n){
  // ...
  document.querySelectorAll('audio[id^="audio-"]').forEach(a=>{a.pause();a.currentTime=0});
  const audioEl = document.getElementById('audio-' + (ix+1).toString().padStart(2,'0'));
  if(audioEl) audioEl.play().catch(()=>{});
  // ...
}
```

**注意**：如果音频文件名包含"第X页"前缀，用户可能会要求去掉。配音文案应直接描述内容，不提页面编号。

## 5. 内容修订策略

**用户偏好**：不要用"修订说明/修改说明"页面来展示变更内容。直接将最终方案呈现在对应页面上，让用户看到的就是最终结果，不需要解释"之前是什么、现在改成什么"。

## 6. 动画性能

- 当幻灯片数量 ≥ 15 时，Motion One 的 `stagger` 动效在低端机上可能卡顿
- 可在 `<body>` 上加 `class="low-power"` 静态模式
- 按 `B` 键可切换动效开关（模板已内置）

## 7. 边距与内容溢出

- 所有文本容器加 `overflow-wrap:break-word`
- 纯中文文本用 `.body-zh`（非衬线）而非 `.body-serif`（衬线正文不易读）
- 卡片内中文描述控制在 ≤ 20 字/行，避免 4 列网格中文字溢出