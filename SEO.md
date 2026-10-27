# hiwd Google SEO 维护

主站规范网址为 `https://hiwd.com/`。HTTP 和 www 由 GitHub Pages 301 跳转到主站；根目录的 `index.html` 使用首页规范网址。

## 发布新文章

1. 按 `AGENTS.md` 写文章，并在 `words.html` 加真实 HTML 链接。
2. 在 HTML 的 head 中写入独立的 title、非空 meta description、完整 canonical、og:title、og:description、og:url、og:site_name；加入 `lang="zh-CN"` 和 `/favicon.ico` 图标链接。
3. 运行 `python3 scripts/seo.py --write-sitemap`，将生成的 `sitemap.xml` 一起提交。
4. 运行 `python3 scripts/seo.py`，检查元数据、规范网址、站内可发现性、robots 和地图是否完整。

网站继续使用纯静态 HTML，不需要安装依赖或增加构建步骤。脚本只使用 Python 3 标准库。站点地图排除 404 页面、跳转页和页脚片段；不填写无法准确维护的 lastmod、priority 或 changefreq。

## 首次配置 Google Search Console

在 https://search.google.com/search-console 中登录自己的 Google 账号。推荐添加 `hiwd.com` 网域资源，并按 Google 给出的值添加 DNS TXT 记录；它可覆盖主站及子域名。如果暂时不能改 DNS，也可以添加 `https://hiwd.com/` 网址前缀资源，用 Google 给出的 HTML 文件或 meta 验证标签完成验证。不要猜测验证值。

验证后：

1. 在「站点地图」提交 `https://hiwd.com/sitemap.xml`。这里只包含主站，daily 等子域名需单独维护自己的地图。
2. 在「网址检查」中检查 `https://hiwd.com/`，先「测试实际网址」，确认允许抓取且可编入索引，再「请求编入索引」。
3. 同样检查 `https://hiwd.com/words.html` 和重点文章。
4. 查看「网页索引编制」、安全问题和人工处置报告。Google 抓取过的历史状态需要在这里确认，公开 HTTP 检查不能替代。
5. 在效果报告按查询词 `hiwd` 和首页 URL 筛选，比较上线前后 28 天的展现、点击、CTR 与平均排名。无痕搜索仍受位置和语言影响，不能作为唯一指标。

## 已核查的事实（2026-10-27）

- 用户提供的 Google `site:hiwd.com` 截图中已出现主站首页及正常摘要，也收录了 daily 子域名。已收录并不保证品牌词排名。
- 修复前首页 HTTP 200，未返回 X-Robots-Tag 限制；HTTP 与 www 均 301 到 HTTPS 主站。
- 修复前 robots.txt 和 sitemap.xml 都返回 404。Google 将 robots.txt 的 404 视为没有抓取限制，因此不能将其定性为「禁止抓取」。
- 修复前首页 title 仅为 hiwd，缺少 description、canonical、Open Graph 及 WebSite 结构化数据；多篇文章也缺少描述或 canonical。

Google 决定是否收录、使用何种摘要和排名，部署元数据不能保证具体名次或生效日期。不要使用删除网址工具修复排名问题，也无需使用已废弃的 sitemap ping。

## 官方参考

- [搜索结果中没有网页信息](https://support.google.com/webmasters/answer/7489871?hl=zh-Hans)
- [robots.txt 状态码处理](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec?hl=zh-cn)
- [搜索摘要与描述](https://developers.google.com/search/docs/appearance/snippet?hl=zh-cn)
- [规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls?hl=zh-cn)
- [网站名称](https://developers.google.com/search/docs/appearance/site-names?hl=zh-cn)
- [站点地图](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap?hl=zh-cn)
