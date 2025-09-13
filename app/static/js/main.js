/**
 * 主要JavaScript功能
 * 包含主题切换、滚动效果、搜索功能等
 */

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有功能
    initThemeToggle();
    initScrollToTop();
    initSearchModal();
    initSmoothScrolling();
    initLazyLoading();
    initTooltips();
    initFormValidation();
    initCodeCopy();
    
    console.log('🚀 Personal Portal initialized');
});

/**
 * 主题切换功能
 */
function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const html = document.documentElement;
    
    if (!themeToggle || !themeIcon) return;
    
    // 获取当前主题
    const currentTheme = localStorage.getItem('theme') || 
                        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    
    // 设置初始主题
    setTheme(currentTheme);
    
    // 监听切换按钮
    themeToggle.addEventListener('click', function() {
        const newTheme = html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
        localStorage.setItem('theme', newTheme);
        
        // 添加切换动画
        themeIcon.style.transform = 'rotate(180deg)';
        setTimeout(() => {
            themeIcon.style.transform = 'rotate(0deg)';
        }, 300);
    });
    
    function setTheme(theme) {
        html.setAttribute('data-bs-theme', theme);
        themeIcon.className = theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
        
        // 更新主题色
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            metaThemeColor.setAttribute('content', theme === 'dark' ? '#212529' : '#ffffff');
        }
    }
    
    // 监听系统主题变化
    window.matchMedia('(prefers-color-scheme: dark)').addListener((e) => {
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });
}

/**
 * 滚动到顶部功能
 */
function initScrollToTop() {
    const scrollTopBtn = document.getElementById('scrollTopBtn');
    if (!scrollTopBtn) return;
    
    // 监听滚动事件
    let scrollTimeout;
    window.addEventListener('scroll', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            if (window.pageYOffset > 300) {
                scrollTopBtn.classList.remove('d-none');
                scrollTopBtn.style.opacity = '1';
            } else {
                scrollTopBtn.style.opacity = '0';
                setTimeout(() => {
                    if (window.pageYOffset <= 300) {
                        scrollTopBtn.classList.add('d-none');
                    }
                }, 300);
            }
        }, 10);
    });
    
    // 点击返回顶部
    scrollTopBtn.addEventListener('click', function(e) {
        e.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

/**
 * 搜索模态框功能
 */
function initSearchModal() {
    const searchModal = document.getElementById('searchModal');
    const searchInput = document.getElementById('search-input');
    
    if (!searchModal || !searchInput) return;
    
    // 模态框显示时聚焦搜索框
    searchModal.addEventListener('shown.bs.modal', function() {
        searchInput.focus();
    });
    
    // 快捷键支持 (Ctrl+K 或 Cmd+K)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const modal = new bootstrap.Modal(searchModal);
            modal.show();
        }
        
        // ESC关闭模态框
        if (e.key === 'Escape') {
            const modal = bootstrap.Modal.getInstance(searchModal);
            if (modal) {
                modal.hide();
            }
        }
    });
    
    // 实时搜索建议 (可选功能)
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length >= 2) {
            searchTimeout = setTimeout(() => {
                fetchSearchSuggestions(query);
            }, 300);
        }
    });
}

/**
 * 获取搜索建议
 */
function fetchSearchSuggestions(query) {
    // 暂时禁用搜索建议API调用，避免Chrome浏览器等待不存在的接口
    console.log('搜索查询:', query, '(建议功能暂时禁用)');
    // TODO: 实现search-suggestions API端点
    /*
    fetch(`/api/search-suggestions?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchSuggestions(data.suggestions);
        })
        .catch(error => {
            console.warn('搜索建议获取失败:', error);
        });
    */
}

/**
 * 显示搜索建议
 */
function displaySearchSuggestions(suggestions) {
    // 这里可以添加搜索建议显示逻辑
    // 暂时留空，后续可以扩展
}

/**
 * 平滑滚动功能
 */
function initSmoothScrolling() {
    // 为锚点链接添加平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            // 检查href是否有效且不仅仅是#
            if (href && href.length > 1) {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    
                    // 更新URL但不触发滚动
                    history.pushState(null, null, href);
                }
            }
        });
    });
}

/**
 * 懒加载功能
 */
function initLazyLoading() {
    // 使用Intersection Observer API进行图片懒加载
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        img.classList.add('fade-in');
                        observer.unobserve(img);
                    }
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });
        
        // 观察所有带有data-src属性的图片
        document.querySelectorAll('img[data-src]').forEach(img => {
            img.classList.add('lazy');
            imageObserver.observe(img);
        });
    }
}

/**
 * 初始化工具提示
 */
function initTooltips() {
    // 初始化Bootstrap工具提示
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl, {
                delay: { show: 500, hide: 100 }
            });
        });
        
        // 初始化弹出框
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
}

/**
 * 表单验证增强
 */
function initFormValidation() {
    // 为所有表单添加Bootstrap验证样式
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // 滚动到第一个错误字段
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        });
        
        // 实时验证
        form.querySelectorAll('input, textarea, select').forEach(field => {
            field.addEventListener('blur', function() {
                if (this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            });
            
            field.addEventListener('input', function() {
                if (this.classList.contains('is-invalid') && this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        });
    });
    
    // 自定义验证消息
    document.querySelectorAll('input[type="email"]').forEach(input => {
        input.addEventListener('invalid', function() {
            if (this.validity.valueMissing) {
                this.setCustomValidity('请填写邮箱地址');
            } else if (this.validity.typeMismatch) {
                this.setCustomValidity('请输入有效的邮箱地址');
            }
        });
        
        input.addEventListener('input', function() {
            this.setCustomValidity('');
        });
    });
}

/**
 * 代码复制功能
 */
function initCodeCopy() {
    // 为代码块添加复制按钮
    document.querySelectorAll('pre code').forEach(code => {
        const pre = code.parentElement;
        if (pre && pre.tagName === 'PRE') {
            const copyBtn = document.createElement('button');
            copyBtn.className = 'btn btn-sm btn-outline-secondary position-absolute top-0 end-0 m-2';
            copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
            copyBtn.title = '复制代码';
            
            pre.style.position = 'relative';
            pre.appendChild(copyBtn);
            
            copyBtn.addEventListener('click', async function() {
                try {
                    await navigator.clipboard.writeText(code.textContent);
                    
                    // 显示成功反馈
                    const originalContent = this.innerHTML;
                    this.innerHTML = '<i class="fas fa-check text-success"></i>';
                    this.classList.remove('btn-outline-secondary');
                    this.classList.add('btn-outline-success');
                    
                    setTimeout(() => {
                        this.innerHTML = originalContent;
                        this.classList.remove('btn-outline-success');
                        this.classList.add('btn-outline-secondary');
                    }, 2000);
                    
                } catch (err) {
                    console.error('复制失败:', err);
                    
                    // 降级复制方法
                    const textArea = document.createElement('textarea');
                    textArea.value = code.textContent;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    
                    // 显示成功消息
                    showToast('代码已复制到剪贴板', 'success');
                }
            });
        }
    });
}

/**
 * 显示Toast消息
 */
function showToast(message, type = 'info', duration = 3000) {
    // 创建toast容器（如果不存在）
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // 创建toast元素
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type}" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // 显示toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: duration });
    toast.show();
    
    // 自动清理
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

/**
 * 工具函数：防抖
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func.apply(this, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(this, args);
    };
}

/**
 * 工具函数：节流
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * 检测设备类型
 */
function getDeviceType() {
    const width = window.innerWidth;
    if (width < 576) return 'mobile';
    if (width < 768) return 'mobile-large';
    if (width < 992) return 'tablet';
    if (width < 1200) return 'desktop';
    return 'desktop-large';
}

/**
 * 性能监控
 */
function trackPerformance() {
    if ('performance' in window) {
        window.addEventListener('load', function() {
            setTimeout(() => {
                const perfData = performance.getEntriesByType('navigation')[0];
                const loadTime = perfData.loadEventEnd - perfData.loadEventStart;
                
                // 可以发送性能数据到分析服务
                console.log('页面加载时间:', loadTime + 'ms');
                
                // 如果加载时间过长，显示提示
                if (loadTime > 3000) {
                    console.warn('页面加载较慢，考虑优化');
                }
            }, 1000);
        });
    }
}

// 启动性能监控
trackPerformance();

/**
 * 错误处理
 */
window.addEventListener('error', function(e) {
    console.error('JavaScript错误:', e.error);
    
    // 在开发环境中显示错误信息
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        showToast('发生了一个错误，请查看控制台', 'error');
    }
});

/**
 * Service Worker注册（PWA支持）
 */
if ('serviceWorker' in navigator && window.location.protocol === 'https:') {
    window.addEventListener('load', function() {
        // 暂时禁用Service Worker注册，避免Chrome等待不存在的sw.js文件
        console.log('Service Worker注册已禁用 (sw.js文件不存在)');
        // TODO: 创建sw.js文件后启用此功能
        /*
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker注册成功:', registration.scope);
            })
            .catch(function(error) {
                console.log('ServiceWorker注册失败:', error);
            });
        */
    });
}

/**
 * 导出主要函数供外部使用
 */
window.PersonalPortal = {
    showToast,
    debounce,
    throttle,
    getDeviceType
};