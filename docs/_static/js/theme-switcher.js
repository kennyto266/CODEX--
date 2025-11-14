/**
 * 主题切换器
 * 支持明暗主题切换，保存用户偏好
 */

(function() {
    'use strict';

    const THEME_STORAGE_KEY = 'sphinx-theme';
    const DARK_THEME_CLASS = 'dark-theme';
    const LIGHT_THEME_CLASS = 'light-theme';

    // 主题配置
    const THEMES = {
        light: {
            name: '浅色',
            icon: '☀️',
            description: '浅色主题'
        },
        dark: {
            name: '深色',
            icon: '🌙',
            description: '深色主题'
        },
        auto: {
            name: '自动',
            icon: '🖥️',
            description: '跟随系统'
        }
    };

    let currentTheme = 'auto';
    let isSystemDark = false;

    /**
     * 初始化主题切换器
     */
    function init() {
        // 获取系统主题偏好
        isSystemDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

        // 读取保存的主题
        const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
        if (savedTheme && THEMES[savedTheme]) {
            currentTheme = savedTheme;
        }

        // 应用主题
        applyTheme(currentTheme);

        // 监听系统主题变化
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                isSystemDark = e.matches;
                if (currentTheme === 'auto') {
                    applyTheme('auto');
                }
            });
        }

        // 创建主题切换按钮
        createThemeToggleButton();
    }

    /**
     * 应用主题
     */
    function applyTheme(theme) {
        const body = document.body;
        const html = document.documentElement;

        // 移除所有主题类
        body.classList.remove(DARK_THEME_CLASS, LIGHT_THEME_CLASS);

        // 确定实际应用的主题
        let actualTheme;
        if (theme === 'auto') {
            actualTheme = isSystemDark ? 'dark' : 'light';
        } else {
            actualTheme = theme;
        }

        // 应用主题类
        body.classList.add(actualTheme === 'dark' ? DARK_THEME_CLASS : LIGHT_THEME_CLASS);

        // 更新meta主题色（移动端状态栏）
        updateMetaThemeColor(actualTheme);

        // 更新Favicon
        updateFavicon(actualTheme);

        // 触发主题变化事件
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme, actualTheme }
        }));

        console.log(`🎨 主题已切换到: ${THEMES[theme].name} (${actualTheme})`);
    }

    /**
     * 更新Meta主题色
     */
    function updateMetaThemeColor(theme) {
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.setAttribute('content', theme === 'dark' ? '#1a1a1a' : '#ffffff');
        }
    }

    /**
     * 更新Favicon
     */
    function updateFavicon(theme) {
        // 这里可以添加根据主题切换Favicon的逻辑
        // 例如：浅色主题使用浅色logo，深色主题使用深色logo
    }

    /**
     * 创建主题切换按钮
     */
    function createThemeToggleButton() {
        // 检查按钮是否已存在
        if (document.getElementById('theme-switcher')) {
            return;
        }

        // 创建按钮容器
        const container = document.createElement('div');
        container.id = 'theme-switcher';
        container.className = 'theme-switcher';

        // 创建按钮
        const button = document.createElement('button');
        button.id = 'theme-toggle-btn';
        button.className = 'theme-toggle-btn';
        button.setAttribute('aria-label', '切换主题');
        button.setAttribute('title', '切换主题');

        // 初始图标
        updateButtonIcon(button, currentTheme);

        // 添加工厂点击事件
        button.addEventListener('click', () => {
            cycleTheme();
            updateButtonIcon(button, currentTheme);
        });

        // 创建下拉菜单
        const dropdown = document.createElement('div');
        dropdown.className = 'theme-dropdown';
        dropdown.style.display = 'none';

        // 创建菜单项
        Object.keys(THEMES).forEach(themeKey => {
            const menuItem = document.createElement('div');
            menuItem.className = 'theme-menu-item';
            menuItem.innerHTML = `
                <span class="theme-icon">${THEMES[themeKey].icon}</span>
                <span class="theme-name">${THEMES[themeKey].name}</span>
            `;

            if (themeKey === currentTheme) {
                menuItem.classList.add('active');
            }

            menuItem.addEventListener('click', (e) => {
                e.stopPropagation();
                currentTheme = themeKey;
                localStorage.setItem(THEME_STORAGE_KEY, currentTheme);
                applyTheme(currentTheme);
                updateButtonIcon(button, currentTheme);
                updateMenuItems(dropdown);
                dropdown.style.display = 'none';
            });

            dropdown.appendChild(menuItem);
        });

        // 关闭下拉菜单
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        // 切换下拉菜单显示
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
        });

        // 组装按钮
        container.appendChild(button);
        container.appendChild(dropdown);
        document.body.appendChild(container);

        // 添加样式
        addThemeSwitcherStyles();
    }

    /**
     * 更新按钮图标
     */
    function updateButtonIcon(button, theme) {
        const icon = THEMES[theme].icon;
        button.innerHTML = icon;
        button.setAttribute('title', `当前主题: ${THEMES[theme].name} (点击切换)`);
    }

    /**
     * 更新菜单项状态
     */
    function updateMenuItems(dropdown) {
        dropdown.querySelectorAll('.theme-menu-item').forEach(item => {
            item.classList.remove('active');
        });

        const activeItem = dropdown.querySelector(`.theme-menu-item:nth-child(${Object.keys(THEMES).indexOf(currentTheme) + 1})`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }

    /**
     * 循环切换主题
     */
    function cycleTheme() {
        const themeKeys = Object.keys(THEMES);
        const currentIndex = themeKeys.indexOf(currentTheme);
        const nextIndex = (currentIndex + 1) % themeKeys.length;
        currentTheme = themeKeys[nextIndex];
        localStorage.setItem(THEME_STORAGE_KEY, currentTheme);
        applyTheme(currentTheme);
    }

    /**
     * 添加主题切换器样式
     */
    function addThemeSwitcherStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .theme-switcher {
                position: fixed;
                bottom: 20px;
                right: 80px;
                z-index: 9999;
            }

            .theme-toggle-btn {
                width: 50px;
                height: 50px;
                border-radius: 50%;
                background: #2980B9;
                color: white;
                border: none;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .theme-toggle-btn:hover {
                transform: scale(1.1);
                background: #1f6391;
            }

            .theme-dropdown {
                position: absolute;
                bottom: 60px;
                right: 0;
                background: white;
                border: 1px solid #e1e4e8;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                min-width: 150px;
                overflow: hidden;
            }

            .theme-menu-item {
                display: flex;
                align-items: center;
                padding: 10px 15px;
                cursor: pointer;
                transition: background 0.2s;
            }

            .theme-menu-item:hover {
                background: #f6f8fa;
            }

            .theme-menu-item.active {
                background: #e3f2fd;
                color: #2980B9;
            }

            .theme-icon {
                font-size: 18px;
                margin-right: 10px;
            }

            .theme-name {
                font-size: 14px;
            }

            /* 暗色主题样式 */
            .dark-theme .theme-dropdown {
                background: #2d2d2d;
                border-color: #444;
            }

            .dark-theme .theme-menu-item {
                color: #e0e0e0;
            }

            .dark-theme .theme-menu-item:hover {
                background: #3d3d3d;
            }

            .dark-theme .theme-menu-item.active {
                background: #1a365d;
                color: #63b3ed;
            }

            /* 响应式 */
            @media (max-width: 768px) {
                .theme-switcher {
                    bottom: 10px;
                    right: 70px;
                }

                .theme-toggle-btn {
                    width: 40px;
                    height: 40px;
                    font-size: 18px;
                }

                .theme-dropdown {
                    bottom: 50px;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // 在DOM加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // 导出全局接口（可选）
    window.ThemeSwitcher = {
        getCurrentTheme: () => currentTheme,
        setTheme: (theme) => {
            if (THEMES[theme]) {
                currentTheme = theme;
                localStorage.setItem(THEME_STORAGE_KEY, currentTheme);
                applyTheme(currentTheme);
            }
        },
        getAvailableThemes: () => ({...THEMES})
    };

})();
