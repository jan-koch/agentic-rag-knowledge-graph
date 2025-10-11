/**
 * RAG Chat Widget - Secure Version with API Key
 *
 * Usage:
 * <script>
 *   window.RAG_CHAT_CONFIG = {
 *     apiKey: 'your-workspace-api-key',
 *     apiUrl: 'https://botapi.kobra-dataworks.de'
 *   };
 * </script>
 * <script src="https://botapi.kobra-dataworks.de/static/chat-widget-secure.js"></script>
 */

(function() {
    // Get configuration from global variable
    const config = window.RAG_CHAT_CONFIG || {};

    if (!config.apiKey) {
        console.error('RAG Chat Widget: ' + (config.language === 'en' ? 'API key is required. Set window.RAG_CHAT_CONFIG.apiKey' : 'API-Schlüssel erforderlich. Setzen Sie window.RAG_CHAT_CONFIG.apiKey'));
        return;
    }

    const apiUrl = config.apiUrl || 'https://botapi.kobra-dataworks.de';
    const primaryColor = config.primaryColor || '#667eea';
    const position = config.position || 'bottom-right';
    const language = config.language || 'de'; // 'en' or 'de'

    // Translations
    const translations = {
        en: {
            error_prefix: 'Chat Widget Error: ',
            api_key_required: 'API key is required. Set window.RAG_CHAT_CONFIG.apiKey',
            invalid_api_key: 'Invalid API key',
            subscription_inactive: 'Subscription is not active',
            validation_failed: 'Validation failed: ',
            not_validated: 'Widget not validated. Please check API key.'
        },
        de: {
            error_prefix: 'Chat-Widget Fehler: ',
            api_key_required: 'API-Schlüssel erforderlich. Setzen Sie window.RAG_CHAT_CONFIG.apiKey',
            invalid_api_key: 'Ungültiger API-Schlüssel',
            subscription_inactive: 'Abonnement ist nicht aktiv',
            validation_failed: 'Validierung fehlgeschlagen: ',
            not_validated: 'Widget nicht validiert. Bitte überprüfen Sie den API-Schlüssel.'
        }
    };

    const t = translations[language];

    // Check if widget is already initialized
    if (window.RagChatWidget) return;

    let workspaceId = null;
    let agentId = null;
    let agentName = 'Support Bot';
    let isValidated = false;

    // Validate API key and get workspace/agent info
    async function validateAndGetConfig() {
        try {
            const response = await fetch(`${apiUrl}/v1/widget/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${config.apiKey}`
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || t.invalid_api_key);
            }

            const data = await response.json();

            // Check subscription status
            if (!data.subscription_active) {
                throw new Error(t.subscription_inactive);
            }

            workspaceId = data.workspace_id;
            agentId = data.agent_id;
            agentName = data.agent_name || 'Support Bot';
            isValidated = true;

            return true;
        } catch (error) {
            console.error('RAG Chat Widget validation failed:', error.message);
            showError(error.message);
            return false;
        }
    }

    // Show error message
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = `
            position: fixed;
            ${position.includes('bottom') ? 'bottom: 20px;' : 'top: 20px;'}
            ${position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
            background: #f44336;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            z-index: 999999;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        `;
        errorDiv.textContent = `${t.error_prefix}${message}`;
        document.body.appendChild(errorDiv);

        setTimeout(() => errorDiv.remove(), 5000);
    }

    // Create widget HTML
    const widgetHTML = `
        <div id="rag-chat-widget" style="
            position: fixed;
            ${position.includes('bottom') ? 'bottom: 20px;' : 'top: 20px;'}
            ${position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
            z-index: 999999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        ">
            <!-- Chat Button -->
            <button id="rag-chat-toggle" style="
                background: linear-gradient(135deg, ${primaryColor} 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                font-size: 28px;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                transition: transform 0.2s, box-shadow 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                outline: none;
            ">
                💬
            </button>

            <!-- Chat Window -->
            <div id="rag-chat-window" style="
                display: none;
                position: absolute;
                ${position.includes('bottom') ? 'bottom: 80px;' : 'top: 80px;'}
                ${position.includes('right') ? 'right: 0;' : 'left: 0;'}
                width: 380px;
                height: 600px;
                max-width: calc(100vw - 40px);
                max-height: calc(100vh - 120px);
                background: white;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.2);
                overflow: hidden;
                animation: slideUp 0.3s ease;
            ">
                <div id="rag-chat-content" style="width: 100%; height: 100%;"></div>
            </div>
        </div>

        <style>
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            #rag-chat-toggle:hover {
                transform: scale(1.05);
                box-shadow: 0 6px 16px rgba(0,0,0,0.2);
            }

            #rag-chat-toggle:active {
                transform: scale(0.95);
            }

            @media (max-width: 640px) {
                #rag-chat-window {
                    width: calc(100vw - 40px) !important;
                    height: calc(100vh - 120px) !important;
                }
            }
        </style>
    `;

    // Load chat iframe
    function loadChat() {
        if (!isValidated) {
            showError(t.not_validated);
            return;
        }

        const chatContent = document.getElementById('rag-chat-content');
        const iframe = document.createElement('iframe');
        iframe.id = 'rag-chat-iframe';

        // Get greeting and language from config
        const greeting = config.greeting || `Hi! I'm ${agentName}. How can I help?`;
        const widgetLanguage = config.language || language || 'de';

        iframe.src = `${apiUrl}/widget/chat?workspace_id=${workspaceId}&agent_id=${agentId}&agent_name=${encodeURIComponent(agentName)}&api_url=${encodeURIComponent(apiUrl)}&greeting=${encodeURIComponent(greeting)}&language=${widgetLanguage}`;
        iframe.style.cssText = 'width: 100%; height: 100%; border: none;';
        iframe.allow = 'clipboard-write';

        chatContent.innerHTML = '';
        chatContent.appendChild(iframe);
    }

    // Initialize widget
    async function initWidget() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initWidget);
            return;
        }

        // Validate API key first
        const isValid = await validateAndGetConfig();
        if (!isValid) {
            return;
        }

        // Create and append widget
        const container = document.createElement('div');
        container.innerHTML = widgetHTML;
        document.body.appendChild(container);

        // Get elements
        const toggleBtn = document.getElementById('rag-chat-toggle');
        const chatWindow = document.getElementById('rag-chat-window');
        let isOpen = false;

        // Toggle chat
        toggleBtn.addEventListener('click', () => {
            isOpen = !isOpen;
            chatWindow.style.display = isOpen ? 'block' : 'none';
            toggleBtn.innerHTML = isOpen ? '✕' : '💬';
            toggleBtn.style.transform = isOpen ? 'rotate(90deg)' : 'rotate(0deg)';

            // Load chat iframe when first opened
            if (isOpen && !document.getElementById('rag-chat-iframe')) {
                loadChat();
            }

            // Focus iframe when opened
            if (isOpen) {
                const iframe = document.getElementById('rag-chat-iframe');
                if (iframe) iframe.focus();
            }
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isOpen) {
                isOpen = false;
                chatWindow.style.display = 'none';
                toggleBtn.innerHTML = '💬';
                toggleBtn.style.transform = 'rotate(0deg)';
            }
        });

        // Public API
        window.RagChatWidget = {
            open: () => {
                if (!isOpen) toggleBtn.click();
            },
            close: () => {
                if (isOpen) toggleBtn.click();
            },
            toggle: () => {
                toggleBtn.click();
            },
            isOpen: () => isOpen,
            reload: async () => {
                const wasOpen = isOpen;
                if (wasOpen) toggleBtn.click();
                await validateAndGetConfig();
                loadChat();
                if (wasOpen) toggleBtn.click();
            }
        };
    }

    // Initialize
    initWidget();
})();
