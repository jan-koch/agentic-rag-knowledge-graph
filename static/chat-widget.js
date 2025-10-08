/**
 * Ihnen Chat Widget - Simple JavaScript Embed
 *
 * Usage: Add this script tag to your HTML:
 * <script src="https://botapi.kobra-dataworks.de/static/chat-widget.js"></script>
 *
 * Or include inline in your HTML
 */

(function() {
    // Configuration - these can be overridden via data attributes
    const config = {
        apiUrl: 'https://botapi.kobra-dataworks.de',
        workspaceId: '518341a0-ae02-4e28-b161-11ea84a392c1',
        agentId: '40ab91a7-a111-48ea-b4cd-f831efeaeff2',
        agentName: 'Ihnen Support Bot',
        primaryColor: '#667eea',
        position: 'bottom-right' // bottom-right, bottom-left, top-right, top-left
    };

    // Check if widget is already initialized
    if (window.IhnenChatWidget) return;

    // Create widget HTML
    const widgetHTML = `
        <div id="ihnen-chat-widget" style="
            position: fixed;
            ${config.position.includes('bottom') ? 'bottom: 20px;' : 'top: 20px;'}
            ${config.position.includes('right') ? 'right: 20px;' : 'left: 20px;'}
            z-index: 999999;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        ">
            <!-- Chat Button -->
            <button id="ihnen-chat-toggle" style="
                background: linear-gradient(135deg, ${config.primaryColor} 0%, #764ba2 100%);
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
            <div id="ihnen-chat-window" style="
                display: none;
                position: absolute;
                ${config.position.includes('bottom') ? 'bottom: 80px;' : 'top: 80px;'}
                ${config.position.includes('right') ? 'right: 0;' : 'left: 0;'}
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
                <iframe
                    id="ihnen-chat-iframe"
                    src="${config.apiUrl}/widget/chat?workspace_id=${config.workspaceId}&agent_id=${config.agentId}&agent_name=${encodeURIComponent(config.agentName)}&api_url=${encodeURIComponent(config.apiUrl)}"
                    style="width: 100%; height: 100%; border: none;"
                    allow="clipboard-write">
                </iframe>
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

            #ihnen-chat-toggle:hover {
                transform: scale(1.05);
                box-shadow: 0 6px 16px rgba(0,0,0,0.2);
            }

            #ihnen-chat-toggle:active {
                transform: scale(0.95);
            }

            @media (max-width: 640px) {
                #ihnen-chat-window {
                    width: calc(100vw - 40px) !important;
                    height: calc(100vh - 120px) !important;
                }
            }
        </style>
    `;

    // Inject widget into page
    function initWidget() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initWidget);
            return;
        }

        // Create and append widget
        const container = document.createElement('div');
        container.innerHTML = widgetHTML;
        document.body.appendChild(container);

        // Get elements
        const toggleBtn = document.getElementById('ihnen-chat-toggle');
        const chatWindow = document.getElementById('ihnen-chat-window');
        let isOpen = false;

        // Toggle chat
        toggleBtn.addEventListener('click', () => {
            isOpen = !isOpen;
            chatWindow.style.display = isOpen ? 'block' : 'none';
            toggleBtn.innerHTML = isOpen ? '✕' : '💬';
            toggleBtn.style.transform = isOpen ? 'rotate(90deg)' : 'rotate(0deg)';

            // Focus iframe when opened
            if (isOpen) {
                const iframe = document.getElementById('ihnen-chat-iframe');
                iframe.focus();
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
        window.IhnenChatWidget = {
            open: () => {
                if (!isOpen) toggleBtn.click();
            },
            close: () => {
                if (isOpen) toggleBtn.click();
            },
            toggle: () => {
                toggleBtn.click();
            },
            isOpen: () => isOpen
        };
    }

    // Initialize
    initWidget();
})();
