// Bot Integrations JavaScript
// Handles AJAX operations for Telegram, WhatsApp, and Instagram bot management

// ===== UTILITY FUNCTIONS =====

function showAlert(type, message, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
}

function showSpinner(buttonElement, originalText) {
    buttonElement.disabled = true;
    buttonElement.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
        ${originalText}
    `;
}

function hideSpinner(buttonElement, originalText) {
    buttonElement.disabled = false;
    buttonElement.innerHTML = originalText;
}

// ===== TELEGRAM BOT FUNCTIONS =====

async function validateTelegramBot() {
    const button = document.querySelector('#telegramModal .btn-primary');
    const originalText = button.innerHTML;
    
    try {
        showSpinner(button, 'Validating...');
        
        const botName = document.getElementById('telegram_bot_name').value;
        const botToken = document.getElementById('telegram_bot_token').value;
        
        if (!botName || !botToken) {
            showAlert('danger', 'Please fill in all fields.', 'telegram-validation-result');
            return;
        }
        
        // Validate token via API
        const response = await fetch('/api/bots/telegram/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                bot_token: botToken
            })
        });
        
        const result = await response.json();
        
        if (result.valid) {
            showAlert('success', `Bot validated successfully! Username: @${result.bot_username}`, 'telegram-validation-result');
            
            // Save bot to database
            await saveTelegramBot(botName, botToken);
        } else {
            showAlert('danger', `Validation failed: ${result.error}`, 'telegram-validation-result');
        }
        
    } catch (error) {
        console.error('Telegram validation error:', error);
        showAlert('danger', 'Network error occurred. Please try again.', 'telegram-validation-result');
    } finally {
        hideSpinner(button, originalText);
    }
}

async function saveTelegramBot(botName, botToken) {
    try {
        const response = await fetch('/api/bots/telegram/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                bot_name: botName,
                bot_token: botToken
            })
        });
        
        if (response.ok) {
            showAlert('success', 'Telegram bot saved successfully! Refreshing page...', 'telegram-validation-result');
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            const error = await response.json();
            showAlert('danger', `Failed to save bot: ${error.error}`, 'telegram-validation-result');
        }
        
    } catch (error) {
        console.error('Save telegram bot error:', error);
        showAlert('danger', 'Failed to save bot. Please try again.', 'telegram-validation-result');
    }
}

async function setTelegramWebhook(botId) {
    const button = event.target;
    const originalText = button.innerHTML;
    
    try {
        showSpinner(button, 'Setting webhook...');
        
        const response = await fetch('/telegram/set-webhook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                bot_id: botId
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert(`Webhook set successfully!\nURL: ${result.webhook_url}`);
            location.reload();
        } else {
            alert(`Failed to set webhook: ${result.error}`);
        }
        
    } catch (error) {
        console.error('Set webhook error:', error);
        alert('Network error occurred. Please try again.');
    } finally {
        hideSpinner(button, originalText);
    }
}

async function removeTelegramBot(botId) {
    if (!confirm('Are you sure you want to remove this Telegram bot?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/bots/telegram/${botId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Bot removed successfully!');
            location.reload();
        } else {
            const error = await response.json();
            alert(`Failed to remove bot: ${error.error}`);
        }
        
    } catch (error) {
        console.error('Remove telegram bot error:', error);
        alert('Network error occurred. Please try again.');
    }
}

// ===== WHATSAPP BUSINESS FUNCTIONS =====

async function validateWhatsAppCredentials() {
    const button = document.querySelector('#whatsappModal .btn-success');
    const originalText = button.innerHTML;
    
    try {
        showSpinner(button, 'Validating...');
        
        const businessName = document.getElementById('whatsapp_business_name').value;
        const appId = document.getElementById('whatsapp_app_id').value;
        const appSecret = document.getElementById('whatsapp_app_secret').value;
        const verifyToken = document.getElementById('whatsapp_verify_token').value;
        const phoneNumberId = document.getElementById('whatsapp_phone_number_id').value;
        
        if (!businessName || !appId || !appSecret || !verifyToken || !phoneNumberId) {
            showAlert('danger', 'Please fill in all fields.', 'whatsapp-validation-result');
            return;
        }
        
        // Validate credentials via API
        const response = await fetch('/api/bots/whatsapp/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                app_id: appId,
                app_secret: appSecret,
                phone_number_id: phoneNumberId
            })
        });
        
        const result = await response.json();
        
        if (result.valid) {
            showAlert('success', result.message, 'whatsapp-validation-result');
            
            // Save account to database
            await saveWhatsAppAccount(businessName, appId, appSecret, verifyToken, phoneNumberId);
        } else {
            showAlert('danger', `Validation failed: ${result.error}`, 'whatsapp-validation-result');
        }
        
    } catch (error) {
        console.error('WhatsApp validation error:', error);
        showAlert('danger', 'Network error occurred. Please try again.', 'whatsapp-validation-result');
    } finally {
        hideSpinner(button, originalText);
    }
}

async function saveWhatsAppAccount(businessName, appId, appSecret, verifyToken, phoneNumberId) {
    try {
        const response = await fetch('/api/bots/whatsapp/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                business_name: businessName,
                app_id: appId,
                app_secret: appSecret,
                verify_token: verifyToken,
                phone_number_id: phoneNumberId
            })
        });
        
        if (response.ok) {
            showAlert('success', 'WhatsApp Business account saved successfully! Refreshing page...', 'whatsapp-validation-result');
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            const error = await response.json();
            showAlert('danger', `Failed to save account: ${error.error}`, 'whatsapp-validation-result');
        }
        
    } catch (error) {
        console.error('Save WhatsApp account error:', error);
        showAlert('danger', 'Failed to save account. Please try again.', 'whatsapp-validation-result');
    }
}

async function removeWhatsAppAccount(accountId) {
    if (!confirm('Are you sure you want to remove this WhatsApp Business account?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/bots/whatsapp/${accountId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Account removed successfully!');
            location.reload();
        } else {
            const error = await response.json();
            alert(`Failed to remove account: ${error.error}`);
        }
        
    } catch (error) {
        console.error('Remove WhatsApp account error:', error);
        alert('Network error occurred. Please try again.');
    }
}

// ===== INSTAGRAM BUSINESS FUNCTIONS =====

async function validateInstagramCredentials() {
    const button = document.querySelector('#instagramModal .btn-primary');
    const originalText = button.innerHTML;
    
    try {
        showSpinner(button, 'Validating...');
        
        const accountName = document.getElementById('instagram_account_name').value;
        const accessToken = document.getElementById('instagram_access_token').value;
        const pageId = document.getElementById('instagram_page_id').value;
        
        if (!accountName || !accessToken || !pageId) {
            showAlert('danger', 'Please fill in all fields.', 'instagram-validation-result');
            return;
        }
        
        // Validate credentials via API
        const response = await fetch('/api/bots/instagram/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                access_token: accessToken,
                page_id: pageId
            })
        });
        
        const result = await response.json();
        
        if (result.valid) {
            showAlert('success', `Account validated successfully! Username: @${result.account_username}`, 'instagram-validation-result');
            
            // Save account to database
            await saveInstagramAccount(accountName, accessToken, pageId);
        } else {
            showAlert('danger', `Validation failed: ${result.error}`, 'instagram-validation-result');
        }
        
    } catch (error) {
        console.error('Instagram validation error:', error);
        showAlert('danger', 'Network error occurred. Please try again.', 'instagram-validation-result');
    } finally {
        hideSpinner(button, originalText);
    }
}

async function saveInstagramAccount(accountName, accessToken, pageId) {
    try {
        const response = await fetch('/api/bots/instagram/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                account_name: accountName,
                access_token: accessToken,
                page_id: pageId
            })
        });
        
        if (response.ok) {
            showAlert('success', 'Instagram Business account saved successfully! Refreshing page...', 'instagram-validation-result');
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            const error = await response.json();
            showAlert('danger', `Failed to save account: ${error.error}`, 'instagram-validation-result');
        }
        
    } catch (error) {
        console.error('Save Instagram account error:', error);
        showAlert('danger', 'Failed to save account. Please try again.', 'instagram-validation-result');
    }
}

async function removeInstagramAccount(accountId) {
    if (!confirm('Are you sure you want to remove this Instagram Business account?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/bots/instagram/${accountId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Account removed successfully!');
            location.reload();
        } else {
            const error = await response.json();
            alert(`Failed to remove account: ${error.error}`);
        }
        
    } catch (error) {
        console.error('Remove Instagram account error:', error);
        alert('Network error occurred. Please try again.');
    }
}

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', function() {
    console.log('Bot integrations JavaScript loaded');
    
    // Clear form fields when modals are hidden
    document.getElementById('telegramModal')?.addEventListener('hidden.bs.modal', function () {
        document.getElementById('telegramForm').reset();
        document.getElementById('telegram-validation-result').innerHTML = '';
    });
    
    document.getElementById('whatsappModal')?.addEventListener('hidden.bs.modal', function () {
        document.getElementById('whatsappForm').reset();
        document.getElementById('whatsapp-validation-result').innerHTML = '';
    });
    
    document.getElementById('instagramModal')?.addEventListener('hidden.bs.modal', function () {
        document.getElementById('instagramForm').reset();
        document.getElementById('instagram-validation-result').innerHTML = '';
    });
});