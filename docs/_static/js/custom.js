/**
 * 港股量化交易系统 - 自定义JavaScript
 * 增强文档的交互性和用户体验
 */

(function() {
    'use strict';

    // 等待DOM加载完成
    document.addEventListener('DOMContentLoaded', function() {
        console.log('📚 港股量化交易系统文档加载完成');

        // 初始化所有功能
        initCodeCopyButtons();
        initSmoothScrolling();
        initTableOfContents();
        initTooltips();
        initProgressIndicator();
        initThemeToggle();
        initCodeBlockToggle();
        initSearchHighlight();
        initAnchorLinks();
        initMobileMenu();

        // 添加页面加载动画
        addPageLoadAnimation();
    });

    /**
     * 初始化代码复制按钮
     */
    function initCodeCopyButtons() {
        const codeBlocks = document.querySelectorAll('.highlight');

        codeBlocks.forEach(block => {
            // 避免重复添加
            if (block.querySelector('.copybtn')) return;

            const button = document.createElement('button');
            button.className = 'copybtn';
            button.textContent = '复制';
            button.title = '复制代码到剪贴板';

            button.addEventListener('click', () => {
                const code = block.querySelector('pre').textContent;
                copyToClipboard(code, button);
            });

            block.appendChild(button);
        });
    }

    /**
     * 复制到剪贴板
     */
    function copyToClipboard(text, button) {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => {
                showCopySuccess(button);
            });
        } else {
            // 降级方案
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            try {
                document.execCommand('copy');
                showCopySuccess(button);
            } catch (err) {
                console.error('复制失败:', err);
                button.textContent = '复制失败';
                setTimeout(() => {
                    button.textContent = '复制';
                }, 2000);
            }

            document.body.removeChild(textArea);
        }
    }

    /**
     * 显示复制成功提示
     */
    function showCopySuccess(button) {
        const originalText = button.textContent;
        button.textContent = '已复制!';
        button.classList.add('copied');

        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    }

    /**
     * 初始化平滑滚动
     */
    function initSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');

                // 跳过空的锚点
                if (href === '#') return;

                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });

                    // 更新地址栏
                    history.pushState(null, null, href);
                }
            });
        });
    }

    /**
     * 初始化目录高亮
     */
    function initTableOfContents() {
        const tocLinks = document.querySelectorAll('.toctree-l1 > a, .toctree-l2 > a, .toctree-l3 > a');

        if (tocLinks.length === 0) return;

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    const id = entry.target.getAttribute('id');
                    const link = document.querySelector(`.toctree-l1 > a[href="#${id}"], .toctree-l2 > a[href="#${id}"], .toctree-l3 > a[href="#${id}"]`);

                    if (link) {
                        if (entry.isIntersecting) {
                            // 移除所有活动状态
                            tocLinks.forEach(l => l.classList.remove('active'));
                            // 添加当前活动状态
                            link.classList.add('active');
                        }
                    }
                });
            },
            {
                rootMargin: '-100px 0px -66% 0px',
                threshold: 0
            }
        );

        // 观察所有标题
        document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(heading => {
            if (heading.id) {
                observer.observe(heading);
            }
        });

        // 添加目录活动状态样式
        const style = document.createElement('style');
        style.textContent = `
            .toctree-l1 > a.active,
            .toctree-l2 > a.active,
            .toctree-l3 > a.active {
                color: #2980B9 !important;
                font-weight: bold;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * 初始化工具提示
     */
    function initTooltips() {
        const elementsWithTooltip = document.querySelectorAll('[title]');

        elementsWithTooltip.forEach(element => {
            const title = element.getAttribute('title');
            if (!title) return;

            element.addEventListener('mouseenter', (e) => {
                showTooltip(e.target, title);
            });

            element.addEventListener('mouseleave', () => {
                hideTooltip();
            });
        });
    }

    /**
     * 显示工具提示
     */
    function showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.textContent = text;
        tooltip.style.cssText = `
            position: absolute;
            background: #333;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            white-space: nowrap;
            z-index: 10000;
            pointer-events: none;
        `;

        document.body.appendChild(tooltip);

        const rect = element.getBoundingClientRect();
        tooltip.style.top = (rect.top - tooltip.offsetHeight - 5 + window.scrollY) + 'px';
        tooltip.style.left = (rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)) + 'px';

        // 自动隐藏
        setTimeout(hideTooltip, 3000);
    }

    /**
     * 隐藏工具提示
     */
    function hideTooltip() {
        const tooltip = document.querySelector('.custom-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    /**
     * 初始化进度指示器
     */
    function initProgressIndicator() {
        // 创建进度条
        const progressBar = document.createElement('div');
        progressBar.id = 'reading-progress';
        progressBar.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 0%;
            height: 3px;
            background: linear-gradient(90deg, #2980B9, #1f6391);
            z-index: 10000;
            transition: width 0.1s;
        `;
        document.body.appendChild(progressBar);

        // 监听滚动事件
        window.addEventListener('scroll', () => {
            const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (winScroll / height) * 100;
            progressBar.style.width = scrolled + '%';
        });
    }

    /**
     * 初始化主题切换
     */
    function initThemeToggle() {
        // 检查系统主题偏好
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const savedTheme = localStorage.getItem('theme');
        const theme = savedTheme || (prefersDark ? 'dark' : 'light');

        if (theme === 'dark') {
            document.body.classList.add('dark-theme');
        }

        // 创建主题切换按钮
        const themeToggle = document.createElement('button');
        themeToggle.id = 'theme-toggle';
        themeToggle.innerHTML = theme === 'dark' ? '☀️' : '🌙';
        themeToggle.title = '切换主题';
        themeToggle.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: #2980B9;
            color: white;
            border: none;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 9999;
            transition: all 0.3s;
        `;

        themeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-theme');
            const isDark = document.body.classList.contains('dark-theme');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            themeToggle.innerHTML = isDark ? '☀️' : '🌙';
        });

        themeToggle.addEventListener('mouseenter', () => {
            themeToggle.style.transform = 'scale(1.1)';
        });

        themeToggle.addEventListener('mouseleave', () => {
            themeToggle.style.transform = 'scale(1)';
        });

        document.body.appendChild(themeToggle);

        // 黑暗主题样式
        const darkThemeStyle = document.createElement('style');
        darkThemeStyle.textContent = `
            .dark-theme {
                filter: invert(1) hue-rotate(180deg);
            }
            .dark-theme img,
            .dark-theme video,
            .dark-theme iframe {
                filter: invert(1) hue-rotate(180deg);
            }
        `;
        document.head.appendChild(darkThemeStyle);
    }

    /**
     * 初始化代码块切换
     */
    function initCodeBlockToggle() {
        const collapsibleBlocks = document.querySelectorAll('.toggle-block');

        collapsibleBlocks.forEach(block => {
            const header = block.querySelector('.toggle-header');
            const content = block.querySelector('.toggle-content');

            if (header && content) {
                header.style.cursor = 'pointer';
                header.addEventListener('click', () => {
                    const isOpen = content.style.display === 'block';
                    content.style.display = isOpen ? 'none' : 'block';
                    header.classList.toggle('open', !isOpen);
                });
            }
        });
    }

    /**
     * 初始化搜索高亮
     */
    function initSearchHighlight() {
        // 如果URL中包含搜索参数，高亮相关文本
        const urlParams = new URLSearchParams(window.location.search);
        const q = urlParams.get('q');

        if (q) {
            highlightSearchTerm(q);
        }
    }

    /**
     * 高亮搜索词
     */
    function highlightSearchTerm(term) {
        if (!term) return;

        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        const textNodes = [];
        let node;

        while (node = walker.nextNode()) {
            if (node.parentElement.tagName !== 'SCRIPT' &&
                node.parentElement.tagName !== 'STYLE' &&
                node.parentElement.className !== 'copybtn') {
                textNodes.push(node);
            }
        }

        textNodes.forEach(textNode => {
            const text = textNode.textContent;
            const regex = new RegExp(`(${term})`, 'gi');
            if (regex.test(text)) {
                const highlightedText = text.replace(regex, '<mark>$1</mark>');
                const wrapper = document.createElement('div');
                wrapper.innerHTML = highlightedText;
                textNode.parentNode.replaceChild(wrapper, textNode);
            }
        });

        // 添加高亮样式
        const style = document.createElement('style');
        style.textContent = `
            mark {
                background: yellow;
                color: black;
                padding: 0 2px;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * 初始化锚点链接
     */
    function initAnchorLinks() {
        document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(heading => {
            if (!heading.id) {
                heading.id = heading.textContent
                    .toLowerCase()
                    .replace(/[^\w]+/g, '-')
                    .replace(/-+$/, '');
            }

            // 添加锚点图标
            const anchor = document.createElement('a');
            anchor.href = '#' + heading.id;
            anchor.className = 'header-anchor';
            anchor.innerHTML = '¶';
            anchor.style.cssText = `
                text-decoration: none;
                color: #ccc;
                margin-left: 10px;
                opacity: 0;
                transition: opacity 0.3s;
            `;

            heading.style.position = 'relative';
            heading.appendChild(anchor);

            heading.addEventListener('mouseenter', () => {
                anchor.style.opacity = '1';
            });

            heading.addEventListener('mouseleave', () => {
                anchor.style.opacity = '0';
            });
        });
    }

    /**
     * 初始化移动端菜单
     */
    function initMobileMenu() {
        // 创建移动端菜单按钮
        const menuButton = document.createElement('button');
        menuButton.id = 'mobile-menu-button';
        menuButton.innerHTML = '☰';
        menuButton.title = '菜单';
        menuButton.style.cssText = `
            display: none;
            position: fixed;
            top: 10px;
            left: 10px;
            width: 50px;
            height: 50px;
            background: #2980B9;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 24px;
            cursor: pointer;
            z-index: 10001;
        `;

        document.body.appendChild(menuButton);

        // 响应式显示
        function checkScreenSize() {
            if (window.innerWidth <= 768) {
                menuButton.style.display = 'block';
            } else {
                menuButton.style.display = 'none';
            }
        }

        window.addEventListener('resize', checkScreenSize);
        checkScreenSize();

        // 菜单点击事件
        menuButton.addEventListener('click', () => {
            document.body.classList.toggle('mobile-menu-open');
        });
    }

    /**
     * 添加页面加载动画
     */
    function addPageLoadAnimation() {
        const elements = document.querySelectorAll('.rst-content > *');
        elements.forEach((el, index) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'all 0.5s ease';

            setTimeout(() => {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, index * 50);
        });
    }

})();
