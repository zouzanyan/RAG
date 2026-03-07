// API 配置
const API_BASE = 'http://localhost:8010/api/v1';

// 全局状态
let chatHistory = [];

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

// 初始化应用
async function initApp() {
    checkHealth();
    loadDocuments();
    loadConfig();

    // 文件选择监听
    document.getElementById('fileInput').addEventListener('change', handleFileSelect);

    // 回车提交查询
    document.getElementById('queryInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            submitQuery();
        }
    });
}

// 检查系统健康状态
async function checkHealth() {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            const data = await response.json();
            statusDot.className = 'status-dot online';
            statusText.textContent = `在线 (v${data.version})`;
            showToast('系统已连接', 'success');
        } else {
            throw new Error('Health check failed');
        }
    } catch (error) {
        statusDot.className = 'status-dot offline';
        statusText.textContent = '离线';
        showToast('无法连接到服务器', 'error');
    }
}

// 加载文档列表
async function loadDocuments() {
    const listContainer = document.getElementById('documentList');

    try {
        const response = await fetch(`${API_BASE}/documents`);
        if (!response.ok) throw new Error('Failed to load documents');

        const data = await response.json();

        if (data.total === 0) {
            listContainer.innerHTML = '<p class="text-muted">暂无文档</p>';
            return;
        }

        listContainer.innerHTML = data.documents.map(doc => `
            <div class="document-item">
                <div>
                    <div class="document-item-name">${doc.filename}</div>
                    <div class="document-item-info">${doc.chunk_count} 个分块</div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        listContainer.innerHTML = '<p class="text-muted">加载失败</p>';
        console.error('Error loading documents:', error);
    }
}

// 加载系统配置
async function loadConfig() {
    const configContainer = document.getElementById('configInfo');

    try {
        const response = await fetch(`${API_BASE}/config`);
        if (!response.ok) throw new Error('Failed to load config');

        const config = await response.json();

        configContainer.innerHTML = `
            <div class="config-item">
                <span class="config-label">嵌入模型</span>
                <span class="config-value">${config.embedding_model}</span>
            </div>
            <div class="config-item">
                <span class="config-label">LLM 模型</span>
                <span class="config-value">${config.llm_model}</span>
            </div>
            <div class="config-item">
                <span class="config-label">Reranker</span>
                <span class="config-value">${config.reranker_enabled ? '启用' : '禁用'}</span>
            </div>
            <div class="config-item">
                <span class="config-label">缓存</span>
                <span class="config-value">${config.cache_enabled ? '启用' : '禁用'}</span>
            </div>
            <div class="config-item">
                <span class="config-label">分块大小</span>
                <span class="config-value">${config.chunk_size}</span>
            </div>
        `;

    } catch (error) {
        configContainer.innerHTML = '<p class="text-muted">加载失败</p>';
        console.error('Error loading config:', error);
    }
}

// 处理文件选择
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    const fileInfo = document.getElementById('fileInfo');
    fileInfo.innerHTML = `
        <strong>已选择:</strong> ${file.name}<br>
        <strong>大小:</strong> ${formatFileSize(file.size)}
    `;
    fileInfo.classList.add('show');

    // 自动上传
    uploadDocument(file);
}

// 上传文档
async function uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    showToast('正在上传文档...', 'info');

    try {
        const response = await fetch(`${API_BASE}/documents/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Upload failed');

        const result = await response.json();

        showToast(
            `上传成功！已切分为 ${result.chunk_count} 个分块`,
            'success'
        );

        // 清空文件选择
        document.getElementById('fileInput').value = '';
        document.getElementById('fileInfo').classList.remove('show');

        // 重新加载文档列表
        loadDocuments();

    } catch (error) {
        showToast('上传失败: ' + error.message, 'error');
        console.error('Error uploading document:', error);
    }
}

// 提交查询
async function submitQuery() {
    const queryInput = document.getElementById('queryInput');
    const query = queryInput.value.trim();

    if (!query) {
        showToast('请输入问题', 'error');
        return;
    }

    // 显示结果卡片
    const resultCard = document.getElementById('resultCard');
    const resultContent = document.getElementById('resultContent');
    const resultMeta = document.getElementById('resultMeta');
    const queryBtn = document.getElementById('queryBtn');

    resultCard.style.display = 'block';
    resultContent.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>思考中...</p>
        </div>
    `;
    resultMeta.innerHTML = '';
    queryBtn.disabled = true;

    const startTime = Date.now();

    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query, use_cache: true })
        });

        if (!response.ok) throw new Error('Query failed');

        const result = await response.json();
        const duration = ((Date.now() - startTime) / 1000).toFixed(2);

        // 显示结果
        resultContent.textContent = result.answer;
        resultMeta.innerHTML = `
            <span>⏱️ ${duration}s</span>
            <span>📦 ${result.cached ? '缓存' : '新查询'}</span>
        `;

        // 添加到历史记录
        addToChatHistory(query, result.answer);

        showToast('查询完成', 'success');

    } catch (error) {
        resultContent.innerHTML = `
            <div style="color: var(--danger-color);">
                ❌ 查询失败: ${error.message}
            </div>
        `;
        showToast('查询失败', 'error');
        console.error('Error querying:', error);
    } finally {
        queryBtn.disabled = false;
    }
}

// 清空查询
function clearQuery() {
    document.getElementById('queryInput').value = '';
    document.getElementById('resultCard').style.display = 'none';
}

// 添加到对话历史
function addToChatHistory(question, answer) {
    const historyContainer = document.getElementById('chatHistory');

    // 移除"暂无记录"提示
    if (chatHistory.length === 0) {
        historyContainer.innerHTML = '';
    }

    chatHistory.push({ question, answer, time: new Date() });

    const chatItem = document.createElement('div');
    chatItem.className = 'chat-item';
    chatItem.innerHTML = `
        <div class="chat-question">❓ ${question}</div>
        <div class="chat-answer">${answer}</div>
        <div class="chat-time">${formatTime(new Date())}</div>
    `;

    historyContainer.insertBefore(chatItem, historyContainer.firstChild);

    // 限制历史记录数量
    if (chatHistory.length > 20) {
        chatHistory.shift();
        historyContainer.removeChild(historyContainer.lastChild);
    }
}

// 显示 Toast 通知
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// 格式化时间
function formatTime(date) {
    return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}
